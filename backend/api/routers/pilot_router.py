import os
import json
import uuid
import requests
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session

from backend.data.database import get_db
from backend.data.models import SystemLogs, VerifiedForecast

# Reportlab imports
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

router = APIRouter(
    prefix="/pilot",
    tags=["pilot"]
)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
DOCS_DIR = os.path.join(DATA_DIR, "documents")
HISTORICAL_DATA_PATH = os.path.join(DATA_DIR, "historical_flight_data.json")
TEMP_MAP_DIR = os.path.join(DATA_DIR, "temp_maps")

os.makedirs(DOCS_DIR, exist_ok=True)
os.makedirs(TEMP_MAP_DIR, exist_ok=True)

class FlightPlanRequest(BaseModel):
    departure: str
    destination: str
    departure_time: str
    area: str
    flight_levels: List[str]
    maps: List[str]

def load_flight_data():
    if os.path.exists(HISTORICAL_DATA_PATH):
        with open(HISTORICAL_DATA_PATH, 'r') as f:
            return json.load(f)
    return {}

def get_live_map(map_type: str, flight_level: str) -> str:
    """Fetches a live map GIF from aviationweather.gov and returns the local filepath."""
    # Mapping to standard public AWC products
    # Using SIGWX Area D as an example.
    # In a fully production system, URLs would be constructed based on level/time dynamically.
    if "SIGWX" in map_type.upper():
        url = "https://aviationweather.gov/data/products/swl/D_sigwx.gif"
    else:
        # Fallback to a generic wind/temp chart
        url = "https://aviationweather.gov/data/products/swh/pgwa_00_fd1.gif"
        
    filename = f"{uuid.uuid4()}.gif"
    filepath = os.path.join(TEMP_MAP_DIR, filename)
    
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            with open(filepath, 'wb') as f:
                f.write(response.content)
            return filepath
    except Exception as e:
        print(f"Failed to fetch live map from {url}: {e}")
        
    return None

def generate_briefing_pdf(filepath: str, req: FlightPlanRequest, duration_mins: int, arrival_time: datetime, forecasts: List[VerifiedForecast]):
    doc = SimpleDocTemplate(filepath, pagesize=A4,
                            rightMargin=30, leftMargin=30,
                            topMargin=30, bottomMargin=18)
    
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    title_style.alignment = 1 # Center
    
    normal_style = styles['Normal']
    
    elements = []
    
    # ----------------------------------------------------
    # 1. EXTENDED WEATHER FORECAST FOR TAKE-OFF (USER'S IMAGE STYLE)
    # ----------------------------------------------------
    
    # Underlined title
    elements.append(Paragraph("<u><b>EXTENDED WEATHER FORECAST FOR TAKE-OFF</b></u>", title_style))
    
    airport_name = "Bandaranaike International Airport - Katunayake"
    if req.departure.upper() == "MRIA":
        airport_name = "Mahinda Rajapaksa International Airport - Mattala"
        
    elements.append(Paragraph(f"<u>{airport_name}</u>", title_style))
    
    issue_time = datetime.utcnow().strftime("%H%M UTC %d %B %Y")
    elements.append(Paragraph(f"<b>Issued Time - {issue_time}</b>", title_style))
    elements.append(Spacer(1, 20))
    
    # Table headers exactly like the image
    table_data = [
        [Paragraph("<b>Time<br/>(hour)</b>"), Paragraph("<b>Wind<br/>(deg/kt)</b>"), Paragraph("<b>Air Temp<br/>(deg C)</b>"), Paragraph("<b>QNH<br/>(hPa)</b>"), Paragraph("<b>Remarks</b>")],
        ["SLST", "UTC", "", "", "", ""] # Subheaders
    ]
    
    # Fill rows with forecast data
    for fc in forecasts:
        utc_time = fc.target_time.strftime("%H%M")
        slst_time = (fc.target_time + timedelta(hours=5, minutes=30)).strftime("%H%M")
        
        wind_str = "VRB05"
        if fc.wind_speed_kts is not None and fc.wind_dir is not None:
            wind_str = f"{int(fc.wind_dir):03d}/{int(fc.wind_speed_kts):02d}"
            
        temp_str = f"{int(fc.dry_temp_c)}" if fc.dry_temp_c is not None else "-"
        qnh_str = f"{int(fc.qnh_hpa)}" if fc.qnh_hpa is not None else "-"
        remarks = fc.clouds if fc.clouds else "-"
        
        table_data.append([slst_time, utc_time, wind_str, temp_str, qnh_str, remarks])
        
    # Formatting table spanning
    # We need to span the columns for Wind, Air Temp, QNH, Remarks over the 2 header rows
    t = Table(table_data, colWidths=[1*inch, 1*inch, 1.5*inch, 1.2*inch, 1*inch, 1.5*inch])
    t.setStyle(TableStyle([
        ('SPAN', (0,0), (1,0)), # Span Time (hour) over SLST and UTC
        ('SPAN', (2,0), (2,1)), # Span Wind
        ('SPAN', (3,0), (3,1)), # Span Air Temp
        ('SPAN', (4,0), (4,1)), # Span QNH
        ('SPAN', (5,0), (5,1)), # Span Remarks
        
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('INNERGRID', (0,0), (-1,-1), 1, colors.black),
        ('BOX', (0,0), (-1,-1), 1, colors.black),
        ('FONTNAME', (0,0), (-1,1), 'Helvetica-Bold'),
        ('FONTNAME', (0,2), (-1,-1), 'Helvetica-Bold'), # Make values bold as in image
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 8),
    ]))
    
    elements.append(t)
    elements.append(Spacer(1, 30))
    
    # ----------------------------------------------------
    # 2. Flight Details Table
    # ----------------------------------------------------
    dep_time_str = datetime.fromisoformat(req.departure_time).strftime("%d-%b-%Y %H:%M Z")
    arr_time_str = arrival_time.strftime("%d-%b-%Y %H:%M Z")
    duration_str = f"{duration_mins // 60}h {duration_mins % 60}m"
    
    data = [
        ["Flight Route", f"{req.departure.upper()} -> {req.destination.upper()}"],
        ["Departure Time", dep_time_str],
        ["Estimated Arrival", arr_time_str],
        ["Est. Flight Time", duration_str],
        ["Requested Area", req.area]
    ]
    
    t2 = Table(data, colWidths=[2*inch, 4*inch])
    t2.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,-1), colors.lightgrey),
        ('TEXTCOLOR', (0,0), (-1,-1), colors.black),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 1, colors.black)
    ]))
    
    elements.append(t2)
    elements.append(Spacer(1, 20))
    elements.append(PageBreak())
    
    # ----------------------------------------------------
    # 3. Weather Maps Section (Live Fetch)
    # ----------------------------------------------------
    elements.append(Paragraph("REQUESTED CHARTS & MAPS", styles['Heading2']))
    elements.append(Spacer(1, 10))
    
    validity_str = f"VALID: {dep_time_str} TO {arr_time_str}"
    
    if not req.flight_levels:
        elements.append(Paragraph("No specific flight levels requested.", normal_style))
    
    for fl in req.flight_levels:
        elements.append(Paragraph(f"Flight Level: {fl}", styles['Heading3']))
        for map_type in req.maps:
            elements.append(Spacer(1, 10))
            
            # Fetch live map image
            map_filepath = get_live_map(map_type, fl)
            
            if map_filepath:
                try:
                    img = RLImage(map_filepath, width=6*inch, height=3.5*inch)
                    # A table to hold the title + image
                    box_data = [[f"{map_type} Chart - {fl} | {validity_str}"], [img]]
                except:
                    box_data = [[f"{map_type} Chart - {fl}\n\n{validity_str}\n\n[ ERROR LOADING MAP IMAGE ]"]]
            else:
                box_data = [[f"{map_type} Chart - {fl}\n\n{validity_str}\n\n[ MAP FETCH TIMEOUT / NOT AVAILABLE ]"]]

            box_table = Table(box_data, colWidths=[6*inch])
            box_table.setStyle(TableStyle([
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('BACKGROUND', (0,0), (-1,-1), colors.whitesmoke),
                ('GRID', (0,0), (-1,-1), 1, colors.grey),
                ('FONTNAME', (0,0), (0,0), 'Helvetica-Bold')
            ]))
            
            elements.append(box_table)
            elements.append(Spacer(1, 10))
            
        elements.append(PageBreak())
        
    doc.build(elements)

@router.post("/flight-plan")
def create_flight_plan(req: FlightPlanRequest, db: Session = Depends(get_db)):
    try:
        # Parse datetime
        dep_dt = datetime.fromisoformat(req.departure_time)
        
        # 1. VERIFY FORECAST EXISTS FOR TIMEFRAME
        # Find verified forecasts from departure time up to +3 hours for the table
        end_dt = dep_dt + timedelta(hours=3)
        forecasts = db.query(VerifiedForecast).filter(
            VerifiedForecast.target_time >= dep_dt,
            VerifiedForecast.target_time <= end_dt
        ).order_by(VerifiedForecast.target_time.asc()).all()
        
        if not forecasts:
            # Check if there is ANY forecast on the same day as a fallback just in case, but strict checking is better
            fallback = db.query(VerifiedForecast).filter(
                VerifiedForecast.target_time >= dep_dt - timedelta(hours=6),
                VerifiedForecast.target_time <= dep_dt + timedelta(hours=6)
            ).order_by(VerifiedForecast.target_time.asc()).all()
            
            if not fallback:
                raise HTTPException(
                    status_code=400, 
                    detail=f"No verified meteorological forecast data available for the requested timeframe ({dep_dt.strftime('%Y-%m-%d %H:%M Z')}). The forecaster has not published data for this time."
                )
            forecasts = fallback[:3] # Use up to 3 fallback records

        # 2. Calculate duration based on historical data
        flight_data = load_flight_data()
        dest_upper = req.destination.upper()
        
        duration_mins = 240 # Fallback 4 hours
        if dest_upper in flight_data:
            duration_mins = flight_data[dest_upper][0]
            
        arrival_dt = dep_dt + timedelta(minutes=duration_mins)
        
        # 3. Generate PDF
        doc_id = str(uuid.uuid4())
        filename = f"briefing_{doc_id}.pdf"
        filepath = os.path.join(DOCS_DIR, filename)
        
        generate_briefing_pdf(filepath, req, duration_mins, arrival_dt, forecasts)
        
        # 4. Log to SystemLogs
        log_entry = SystemLogs(
            level="info",
            component=f"Pilot_{req.departure.upper()}_{req.destination.upper()}",
            message="Flight Briefing Document Generated",
            details=json.dumps({
                "departure": req.departure.upper(),
                "destination": req.destination.upper(),
                "duration_mins": duration_mins,
                "flight_levels": req.flight_levels,
                "document_url": f"/documents/{filename}"
            })
        )
        db.add(log_entry)
        db.commit()
        
        return {
            "success": True,
            "document_url": f"http://localhost:8000/documents/{filename}",
            "duration_mins": duration_mins,
            "arrival_time": arrival_dt.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
