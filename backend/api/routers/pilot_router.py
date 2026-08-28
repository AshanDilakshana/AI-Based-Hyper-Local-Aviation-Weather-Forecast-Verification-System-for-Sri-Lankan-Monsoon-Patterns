import os
import json
import uuid
import requests
import time
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List
from sqlalchemy.orm import Session

from backend.data.database import get_db
from backend.data.models import SystemLogs, VerifiedForecast, RouteAlternatives

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image as RLImage, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

router = APIRouter(prefix="/pilot", tags=["pilot"])

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

def get_forecast_hour(duration_mins: int) -> str:
    hours = duration_mins / 60.0
    if hours <= 6: return "06"
    elif hours <= 12: return "12"
    elif hours <= 18: return "18"
    elif hours <= 24: return "24"
    elif hours <= 30: return "30"
    else: return "36"

MAP_URL_CACHE = {}

def get_live_map(map_type: str, flight_level: str, area: str, forecast_hour: str) -> str:
    area_code = area.split()[-1].lower() if "Area" in area else "d"
    fl_code = flight_level.replace("FL", "") if "FL" in flight_level else "340"
    if "SIGWX" in map_type.upper():
        url = f"https://aviationweather.gov/data/products/fax/F24_sigwx_hi_e.gif"
    else:
        url = f"https://aviationweather.gov/data/products/fax/F{forecast_hour}_wind_{fl_code}_{area_code}.gif"
        
    if url in MAP_URL_CACHE and os.path.exists(MAP_URL_CACHE[url]):
        return MAP_URL_CACHE[url]
        
    filename = f"{uuid.uuid4()}.gif"
    filepath = os.path.join(TEMP_MAP_DIR, filename)
    
    try:
        time.sleep(1.5)
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            with open(filepath, 'wb') as f:
                f.write(response.content)
            MAP_URL_CACHE[url] = filepath
            return filepath
        return None
    except:
        return None

def fetch_tafs(airports: List[str]) -> str:
    if not airports:
        return "No alternative airports found."
    url = f"https://aviationweather.gov/api/data/taf?ids={','.join(airports)}&format=raw"
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200 and res.text.strip():
            return res.text
        return "TAF data not available from NOAA."
    except:
        return "Failed to fetch TAF data."

def generate_briefing_pdf(filepath: str, req: FlightPlanRequest, duration_mins: int, arrival_time: datetime, forecasts: List[VerifiedForecast], taf_text: str):
    doc = SimpleDocTemplate(filepath, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=18)
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    title_style.alignment = 1 # Center
    normal_style = styles['Normal']
    
    elements = []
    
    # --- PAGE 1: COVER PAGE ---
    # Top Text
    elements.append(Paragraph("<b>Serial No: - FF / 2023 / 11 / 02</b>", ParagraphStyle(name='Right', alignment=2, fontName='Helvetica-Bold')))
    elements.append(Spacer(1, 15))
    
    # Emblem
    emblem_img_path = "/Users/Ashan/.gemini/antigravity-ide/brain/19078c78-6553-4706-8666-a7303377bb60/.user_uploaded/media_1787944037304.png"
    if os.path.exists(emblem_img_path):
        try:
            img = RLImage(emblem_img_path, width=1.5*inch, height=1.5*inch)
            elements.append(img)
            elements.append(Spacer(1, 5))
        except:
            pass

    # Sinhala text (cropped)
    sinhala_img_path = os.path.join(os.path.dirname(__file__), "sinhala_text.png")
    if os.path.exists(sinhala_img_path):
        try:
            img = RLImage(sinhala_img_path, width=4*inch, height=0.4*inch)
            elements.append(img)
            elements.append(Spacer(1, 5))
        except:
            pass
            
    elements.append(Paragraph("DEPARTMENT OF METEOROLOGY, SRI LANKA", ParagraphStyle(name='CenterHeading', alignment=1, fontName='Helvetica-Bold', fontSize=14)))
    elements.append(Spacer(1, 15))
    elements.append(Paragraph("<b>METEOROLOGICAL CONDITIONS<br/>EN ROUTE<br/>and at<br/>AERODROMES</b>", ParagraphStyle(name='CenterNormal', alignment=1, fontSize=11, leading=14)))
    elements.append(Spacer(1, 15))
    
    # Airplane
    airplane_img_path = "/Users/Ashan/.gemini/antigravity-ide/brain/19078c78-6553-4706-8666-a7303377bb60/.user_uploaded/media_1787946050280.png"
    if os.path.exists(airplane_img_path):
        try:
            img = RLImage(airplane_img_path, width=5.5*inch, height=4*inch, kind='proportional')
            elements.append(img)
            elements.append(Spacer(1, 15))
        except:
            pass
            
    # Flight details
    flight_no = req.area.split('-')[0].strip() if '-' in req.area else '___'
    flight_info = f"<b>Flight No. : &nbsp;&nbsp;&nbsp; <u><i>{flight_no}</i></u> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Route: {req.departure.upper()} - <u><i>{req.destination.upper()}</i></u></b>"
    elements.append(Paragraph(flight_info, ParagraphStyle(name='CenterLarge', alignment=1, fontSize=14, fontName='Helvetica-Bold')))
    elements.append(Spacer(1, 15))
    
    elements.append(Paragraph("<b>Issued by main Meteorological Office at Bandaranaike International Airport, Katunayake.</b>", ParagraphStyle(name='CenterSmall', alignment=1, fontSize=9, fontName='Helvetica-Bold')))
    elements.append(Spacer(1, 5))
    issue_time = datetime.utcnow().strftime("%d %B %Y")
    
    elements.append(Paragraph(f"<b>Date: &nbsp;&nbsp; {issue_time}</b>", ParagraphStyle(name='DateLeft', alignment=0, fontSize=10, fontName='Helvetica-Bold', leftIndent=40)))
    elements.append(Spacer(1, 20))
    
    elements.append(Paragraph("<b>CGP</b>", ParagraphStyle(name='CenterBold14', alignment=1, fontSize=14, fontName='Helvetica-Bold')))
    elements.append(Spacer(1, 5))
    elements.append(Paragraph("................................................................", ParagraphStyle(name='CenterSmall', alignment=1, fontSize=10)))
    elements.append(Paragraph("<b>(Duty Meteorologist)</b>", ParagraphStyle(name='CenterSmall', alignment=1, fontSize=10, fontName='Helvetica-Bold')))
    elements.append(Spacer(1, 20))
    
    # Take Off Data Table (Only the exact departure hour, i.e., the first forecast)
    elements.append(Paragraph("<b>TAKE OFF DATA AT</b>", ParagraphStyle(name='CenterSmall', alignment=1, fontSize=10, fontName='Helvetica-Bold')))
    elements.append(Spacer(1, 5))
    
    takeoff_fc = forecasts[0] if forecasts else None
    t_utc = takeoff_fc.target_time.strftime("%H%M") if takeoff_fc and takeoff_fc.target_time else "-"
    t_wind = f"VRB05"
    if takeoff_fc and takeoff_fc.wind_dir is not None and takeoff_fc.wind_speed_kts is not None:
         t_wind = f"{int(takeoff_fc.wind_dir):03d}{int(takeoff_fc.wind_speed_kts):02d}"
         
    t_temp = f"{int(takeoff_fc.dry_temp_c)}" if takeoff_fc and takeoff_fc.dry_temp_c else "26"
    t_qnh = f"{int(takeoff_fc.qnh_hpa)}" if takeoff_fc and takeoff_fc.qnh_hpa else "1009"
    
    table_data = [
        [Paragraph("<b>TIME<br/>(UTC)</b>", ParagraphStyle(name='c', alignment=1, fontSize=9, fontName='Helvetica-Bold')), 
         Paragraph("<b>SURFACE WIND<br/>(KTS)</b>", ParagraphStyle(name='c', alignment=1, fontSize=9, fontName='Helvetica-Bold')), 
         Paragraph("<b>SURFACE TEMPERATURE<br/>(°C)</b>", ParagraphStyle(name='c', alignment=1, fontSize=9, fontName='Helvetica-Bold')), 
         Paragraph("<b>QNH<br/>(hPa)</b>", ParagraphStyle(name='c', alignment=1, fontSize=9, fontName='Helvetica-Bold'))],
        [Paragraph(f"<font name='Courier-Bold' size=10>{t_utc}</font>", ParagraphStyle(name='c', alignment=1)), 
         Paragraph(f"<font name='Courier-Bold' size=10>{t_wind}</font>", ParagraphStyle(name='c', alignment=1)), 
         Paragraph(f"<font name='Courier-Bold' size=10>{t_temp}</font>", ParagraphStyle(name='c', alignment=1)), 
         Paragraph(f"<font name='Courier-Bold' size=10>{t_qnh}</font>", ParagraphStyle(name='c', alignment=1))],
        ["", "", "", ""]
    ]
    t = Table(table_data, colWidths=[1*inch, 2.2*inch, 2.5*inch, 1*inch])
    t.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('INNERGRID', (0,0), (-1,-1), 1, colors.black),
        ('BOX', (0,0), (-1,-1), 1, colors.black),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('TOPPADDING', (0,0), (-1,-1), 5),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 20))
    
    # HRI Ascent
    elements.append(Paragraph("<b>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; HRI &nbsp; ASCENT &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; (FL 185)</b>", ParagraphStyle(name='LeftBold', alignment=0, fontSize=10, fontName='Helvetica-Bold', leftIndent=150)))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph("<b>03010 &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; -05</b>", ParagraphStyle(name='LeftBold', alignment=0, fontSize=11, fontName='Helvetica-Bold', leftIndent=100)))
    elements.append(Paragraph("<b>WIND .............................. KT &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; TEMP .............................. °C</b>", ParagraphStyle(name='LeftBold', alignment=0, fontSize=10, fontName='Helvetica-Bold', leftIndent=50)))
    
    elements.append(PageBreak())
    
    # --- PAGE 2: STATIC LEGENDS FROM UPLOADED IMAGE ---
    legend1 = "/Users/Ashan/.gemini/antigravity-ide/brain/19078c78-6553-4706-8666-a7303377bb60/.user_uploaded/media_1787944602902.png"
    
    if os.path.exists(legend1):
        # 1024x677 aspect ratio ~ 1.51
        # If width is 7.5 inches, height should be ~ 4.96 inches
        elements.append(Spacer(1, 40))
        elements.append(RLImage(legend1, width=7.5*inch, height=4.96*inch))
        elements.append(PageBreak())
        
    # --- PAGE 4: EXTENDED FORECAST & TAF ---
    airport_name_full = "Bandaranaike International Airport - Katunayake"
    office_name = "METEOROLOGICAL OFFICE - KATUNAYAKE"
    contact_tp = "+94 11 2252721"
    contact_fax = "+94 11 2252319"
    contact_email = "met.katunayake@gmail.com"
    
    if req.departure.upper() == "MRIA": 
        airport_name_full = "Mahinda Rajapaksa International Airport - Mattala"
        office_name = "METEOROLOGICAL OFFICE - MATTALA"
        contact_tp = "+94 47 2031488/2031489"
        contact_fax = "+94 47 2031485"
        contact_email = "met.mattala@gmail.com"
    
    emblem_img_path = "/Users/Ashan/.gemini/antigravity-ide/brain/19078c78-6553-4706-8666-a7303377bb60/.user_uploaded/media_1787944037304.png"
    emblem_flowable = ""
    if os.path.exists(emblem_img_path):
        try:
            emblem_flowable = RLImage(emblem_img_path, width=0.8*inch, height=0.8*inch)
        except:
            pass

    header_text = f"<b>DEPARTMENT OF METEOROLOGY – SRI LANKA</b><br/>{office_name}"
    contact_text = f"<b>Tp:</b> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; {contact_tp}<br/><b>Fax:</b> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; {contact_fax}<br/><b>E-mail:</b> &nbsp;&nbsp; {contact_email}"
    
    header_table = Table([
        [emblem_flowable, Paragraph(header_text, ParagraphStyle(name='H', fontSize=10, leading=14)), Paragraph(contact_text, ParagraphStyle(name='C', fontSize=8, leading=12))]
    ], colWidths=[1*inch, 4*inch, 2.5*inch])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LINEBELOW', (0,0), (-1,-1), 1, colors.black),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 10))
    
    flight_no = req.area.split('-')[0].strip() if '-' in req.area else '___'
    flight_reg_text = f"<b>FLIGHT REGISTRATION NO &nbsp;&nbsp;&nbsp; : &nbsp;&nbsp; {flight_no}</b><br/><b>DESTINATION &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; : &nbsp;&nbsp; {req.destination.upper()}</b>"
    elements.append(Paragraph(flight_reg_text, ParagraphStyle(name='Mono10', fontName='Courier-Bold', fontSize=10, leading=14)))
    elements.append(Spacer(1, 15))
    
    elements.append(Paragraph(f"<u><b>EXTENDED WEATHER FORECAST FOR TAKE-OFF</b></u>", ParagraphStyle(name='CH', alignment=1, fontSize=11, fontName='Helvetica-Bold')))
    elements.append(Paragraph(airport_name_full, ParagraphStyle(name='CN', alignment=1, fontSize=10)))
    issue_time_str = datetime.utcnow().strftime("%H%M UTC %d %B %Y")
    elements.append(Paragraph(f"<b>Issued Time</b> - {issue_time_str}", ParagraphStyle(name='CN', alignment=1, fontSize=10)))
    elements.append(Spacer(1, 10))
    
    ext_table_data = [
        [Paragraph("<b>Time<br/>(hour)</b>", ParagraphStyle(name='c', alignment=1, fontSize=9)), 
         Paragraph("<b>Wind<br/>(deg/kt)</b>", ParagraphStyle(name='c', alignment=1, fontSize=9)), 
         Paragraph("<b>Air Temp<br/>(deg C)</b>", ParagraphStyle(name='c', alignment=1, fontSize=9)), 
         Paragraph("<b>QNH<br/>(hPa)</b>", ParagraphStyle(name='c', alignment=1, fontSize=9)), 
         Paragraph("<b>Remarks</b>", ParagraphStyle(name='c', alignment=1, fontSize=9))],
        [Paragraph("SLST", ParagraphStyle(name='c', alignment=1, fontSize=9)), 
         Paragraph("UTC", ParagraphStyle(name='c', alignment=1, fontSize=9)), 
         "", "", ""]
    ]
    
    for fc in forecasts:
        utc_time = fc.target_time.strftime("%H%M") if fc.target_time else "-"
        slst_time = (fc.target_time + timedelta(hours=5, minutes=30)).strftime("%H%M") if fc.target_time else "-"
        wind_str = "VRB05"
        if fc.wind_speed_kts is not None and fc.wind_dir is not None:
             wind_str = f"{int(fc.wind_dir):03d}{int(fc.wind_speed_kts):02d}"
             
        temp_str = f"{int(fc.dry_temp_c)}" if fc.dry_temp_c is not None else "-"
        qnh_str = f"{int(fc.qnh_hpa)}" if fc.qnh_hpa is not None else "-"
        remarks = fc.remarks if fc.remarks else (fc.clouds if fc.clouds else "-")
        
        ext_table_data.append([
            Paragraph(slst_time, ParagraphStyle(name='c', alignment=1, fontSize=10, fontName='Courier')), 
            Paragraph(utc_time, ParagraphStyle(name='c', alignment=1, fontSize=10, fontName='Courier')), 
            Paragraph(f"<b>{wind_str}</b>", ParagraphStyle(name='c', alignment=1, fontSize=10, fontName='Helvetica-Bold')), 
            Paragraph(f"<b>{temp_str}</b>", ParagraphStyle(name='c', alignment=1, fontSize=10, fontName='Helvetica-Bold')), 
            Paragraph(f"<b>{qnh_str}</b>", ParagraphStyle(name='c', alignment=1, fontSize=10, fontName='Helvetica-Bold')), 
            Paragraph(f"<b>{remarks}</b>", ParagraphStyle(name='c', alignment=1, fontSize=10, fontName='Helvetica-Bold'))
        ])
        
    t3 = Table(ext_table_data, colWidths=[1*inch, 1*inch, 1.8*inch, 1.2*inch, 1*inch, 1.5*inch])
    t3.setStyle(TableStyle([
        ('SPAN', (0,0), (1,0)), 
        ('SPAN', (2,0), (2,1)), 
        ('SPAN', (3,0), (3,1)), 
        ('SPAN', (4,0), (4,1)), 
        ('SPAN', (5,0), (5,1)), 
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('INNERGRID', (0,0), (-1,-1), 1, colors.black),
        ('BOX', (0,0), (-1,-1), 1, colors.black),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('TOPPADDING', (0,0), (-1,-1), 5),
    ]))
    elements.append(t3)
    elements.append(Spacer(1, 10))
    elements.append(Paragraph("<b>Note:</b> This forecast may be amended at any time. For clarification of meteorological issues, please contact Duty Meteorologist.", ParagraphStyle(name='SmallMono', fontSize=8, fontName='Courier')))
    elements.append(Spacer(1, 15))
    
    elements.append(Paragraph("<u><b>TAF & METAR BULLETIN</b></u>", ParagraphStyle(name='CH', alignment=1, fontSize=11, fontName='Helvetica-Bold')))
    elements.append(Spacer(1, 5))
    
    # 2-column TAF layout (Multi-row for safe pagination)
    import re
    taf_blocks = re.split(r'(?=TAF )', taf_text)
    taf_blocks = [b.strip() for b in taf_blocks if b.strip()]
    
    half = (len(taf_blocks) + 1) // 2
    left_blocks = taf_blocks[:half]
    right_blocks = taf_blocks[half:]
    
    taf_style = ParagraphStyle(name='Taf', fontName='Courier', fontSize=8, leading=10)
    taf_rows = []
    
    for i in range(half):
        left_p = Paragraph(left_blocks[i].replace('\n', '<br/>'), taf_style) if i < len(left_blocks) else Paragraph("", taf_style)
        right_p = Paragraph(right_blocks[i].replace('\n', '<br/>'), taf_style) if i < len(right_blocks) else Paragraph("", taf_style)
        taf_rows.append([left_p, right_p])
    
    if not taf_rows:
        taf_rows.append([Paragraph("No TAF Data", taf_style), Paragraph("", taf_style)])
        
    taf_table = Table(taf_rows, colWidths=[3.75*inch, 3.75*inch])
    taf_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOX', (0,0), (0,-1), 1, colors.black), # Border around col 1 continuously
        ('BOX', (1,0), (1,-1), 1, colors.black), # Border around col 2 continuously
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    elements.append(taf_table)
    elements.append(PageBreak())
    
    # --- MAPS ---
    dep_time_str = datetime.fromisoformat(req.departure_time).strftime("%d-%b-%Y %H:%M Z")
    arr_time_str = arrival_time.strftime("%d-%b-%Y %H:%M Z")
    validity_str = f"VALID: {dep_time_str} TO {arr_time_str}"
    
    forecast_hour = get_forecast_hour(duration_mins)
    
    for fl in req.flight_levels:
        for map_type in req.maps:
            elements.append(Paragraph(f"Flight Level: {fl}", styles['Heading3']))
            elements.append(Spacer(1, 10))
            
            map_filepath = get_live_map(map_type, fl, req.area, forecast_hour)
            
            if map_filepath and os.path.exists(map_filepath):
                try:
                    # Make it larger but maintain aspect ratio to prevent cropping/stretching
                    img = RLImage(map_filepath, width=7.2*inch, height=7*inch, kind='proportional')
                    box_data = [[f"{map_type} Chart - {fl} | {validity_str}"], [img]]
                except:
                    box_data = [[f"{map_type} Chart - {fl}\n\n{validity_str}\n\n[ ERROR LOADING MAP IMAGE ]"]]
            else:
                box_data = [[f"{map_type} Chart - {fl}\n\n{validity_str}\n\n[ MAP FETCH TIMEOUT / NOT AVAILABLE ]"]]

            box_table = Table(box_data, colWidths=[7.2*inch])
            box_table.setStyle(TableStyle([
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('BACKGROUND', (0,0), (-1,-1), colors.whitesmoke),
                ('GRID', (0,0), (-1,-1), 1, colors.grey),
                ('FONTNAME', (0,0), (0,0), 'Helvetica-Bold')
            ]))
            elements.append(box_table)
            elements.append(PageBreak())
            
    # --- SECOND LEGEND (SIGNIFICANT WEATHER) ---
    legend2_path = "/Users/Ashan/.gemini/antigravity-ide/brain/19078c78-6553-4706-8666-a7303377bb60/.user_uploaded/media_1787945542625.png"
    if os.path.exists(legend2_path):
        try:
            img = RLImage(legend2_path, width=7.2*inch, height=9.5*inch, kind='proportional')
            elements.append(img)
            elements.append(PageBreak())
        except:
            pass
            
    # --- THIRD LEGEND (LOCATION INDICATORS) ---
    legend3_path = "/Users/Ashan/.gemini/antigravity-ide/brain/19078c78-6553-4706-8666-a7303377bb60/.user_uploaded/media_1787945596169.png"
    if os.path.exists(legend3_path):
        try:
            img = RLImage(legend3_path, width=7.2*inch, height=9.5*inch, kind='proportional')
            elements.append(img)
            # No need for PageBreak() on the absolute last page
        except:
            pass
        
    doc.build(elements)

@router.post("/flight-plan")
def create_flight_plan(req: FlightPlanRequest, db: Session = Depends(get_db)):
    try:
        # Parse datetime and make naive
        dep_dt = datetime.fromisoformat(req.departure_time).replace(tzinfo=None)
        
        # TIME LOGIC: Departure Time up to +3 hours (to get 3 hourly records)
        end_dt = dep_dt + timedelta(hours=3)
        forecasts = db.query(VerifiedForecast).filter(
            VerifiedForecast.target_time >= dep_dt - timedelta(minutes=30),
            VerifiedForecast.target_time <= end_dt
        ).order_by(VerifiedForecast.target_time.asc()).limit(3).all()
        
        if not forecasts:
            # Fallback
            fallback = db.query(VerifiedForecast).filter(
                VerifiedForecast.target_time >= dep_dt - timedelta(hours=6),
                VerifiedForecast.target_time <= dep_dt + timedelta(hours=6)
            ).order_by(VerifiedForecast.target_time.asc()).limit(3).all()
            
            if not fallback:
                raise HTTPException(
                    status_code=400, 
                    detail=f"No verified meteorological forecast data available for the requested timeframe ({dep_dt.strftime('%Y-%m-%d %H:%M Z')})."
                )
            forecasts = fallback

        flight_data = load_flight_data()
        dest_upper = req.destination.upper()
        duration_mins = flight_data.get(dest_upper, [240])[0]
        arrival_dt = dep_dt + timedelta(minutes=duration_mins)
        
        # Find matching route alternatives
        matching_route = db.query(RouteAlternatives).filter(RouteAlternatives.airports.like(f"%{dest_upper}%")).first()
        airports_list = []
        if matching_route:
            airports_list = matching_route.airports.split()
        else:
            # Fallback just use the destination and departure
            airports_list = [req.departure.upper(), dest_upper]
            
        taf_text = fetch_tafs(airports_list)
        
        doc_id = str(uuid.uuid4())
        filename = f"briefing_{doc_id}.pdf"
        filepath = os.path.join(DOCS_DIR, filename)
        
        generate_briefing_pdf(filepath, req, duration_mins, arrival_dt, forecasts, taf_text)
        
        log_entry = SystemLogs(
            level="info",
            component=f"Pilot_{req.departure.upper()}_{req.destination.upper()}",
            message="Flight Briefing Document Generated",
            details=json.dumps({
                "departure": req.departure.upper(),
                "destination": req.destination.upper(),
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
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
