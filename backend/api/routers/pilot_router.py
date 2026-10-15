import os
import json
import uuid
import requests
import time
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session

from backend.data.database import get_db
from backend.data.models import (
    SystemLogs,
    VerifiedForecast,
    RouteAlternatives,
    FlightTimeAndFlights,
    PilotFlightPlan,
)

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    Image as RLImage,
    KeepTogether,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.fonts import addMapping

try:
    # Define the font directory (backend/assets/fonts)
    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    font_dir = os.path.join(backend_dir, "assets", "fonts")
    
    # First try the FM font for legacy encoding
    fm_font_path = os.path.join(font_dir, "FM Ababld-Bold.TTF")
    if os.path.exists(fm_font_path):
        print(f"Found FMSinhala at {fm_font_path}")
        pdfmetrics.registerFont(TTFont("FMSinhala", fm_font_path))
        addMapping("FMSinhala", 0, 0, "FMSinhala")
        pdfmetrics.registerFont(TTFont("fmsinhala", fm_font_path))
        addMapping("fmsinhala", 0, 0, "fmsinhala")

    # Fallback Unicode font
    font_path = os.path.join(font_dir, "NotoSansSinhala-Regular.ttf")
    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont("NotoSinhala", font_path))
        addMapping("NotoSinhala", 0, 0, "NotoSinhala")
        print("Successfully loaded NotoSinhala")
except Exception as e:
    print(f"ERROR LOADING FONTS: {e}")
    import traceback
    traceback.print_exc()


def draw_page_border(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.black)
    canvas.setLineWidth(2)
    canvas.rect(20, 20, doc.pagesize[0] - 40, doc.pagesize[1] - 40)
    canvas.restoreState()


router = APIRouter(prefix="/pilot", tags=["pilot"])

DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data"
)
DOCS_DIR = os.path.join(DATA_DIR, "documents")
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
    pilot_reference: Optional[str] = "guest"
    flight_no: Optional[str] = ""
    preview_only: bool = False
    preview_url: Optional[str] = None


def get_noaa_model_base_time(ref_time: Optional[datetime] = None) -> datetime:
    """
    Returns the estimated base run time (00, 06, 12, or 18 UTC) of the latest
    numerical weather prediction model cycle published on NOAA fax.
    A synoptic run is typically published ~3.5 to 4 hours after its synoptic hour.
    """
    if ref_time is None:
        ref_time = datetime.utcnow()
    effective = ref_time - timedelta(hours=3, minutes=45)
    base_hour = (effective.hour // 6) * 6
    return effective.replace(hour=base_hour, minute=0, second=0, microsecond=0)


def get_forecast_lead_times(
    dep_dt: datetime, duration_mins: int, base_dt: Optional[datetime] = None
) -> List[str]:
    """
    Calculates the exact NOAA forecast lead times (F06, F12, F18, F24, F30, F36)
    corresponding to the flight's departure and en-route/arrival stages from the model run.
    """
    if base_dt is None:
        base_dt = get_noaa_model_base_time()

    dep_lead = (dep_dt - base_dt).total_seconds() / 3600.0
    arr_lead = dep_lead + (duration_mins / 60.0)

    # If the flight date is historical or far future, map by time-of-day offset
    if dep_lead < 0 or dep_lead > 48:
        dep_lead = float((dep_dt.hour - base_dt.hour) % 24)
        if dep_lead < 3:
            dep_lead += 24.0
        arr_lead = dep_lead + (duration_mins / 60.0)

    def find_closest_fh(lead_hours: float) -> int:
        clamped = max(6, min(36, round(lead_hours / 6.0) * 6))
        return int(clamped)

    dep_fh = find_closest_fh(dep_lead)
    arr_fh = find_closest_fh(arr_lead)

    fhs = [dep_fh]
    if arr_fh != dep_fh and (duration_mins / 60.0) >= 5.0:
        fhs.append(arr_fh)

    return [f"{fh:02d}" for fh in fhs]


def get_forecast_hours(duration_mins: int) -> List[str]:
    return get_forecast_lead_times(datetime.utcnow(), duration_mins)


def get_forecast_hour(duration_mins: int) -> str:
    return get_forecast_hours(duration_mins)[-1]


def get_live_map(
    map_type: str, flight_level: str, area: str, forecast_hour: str
) -> str:
    area_code = area.split()[-1].lower() if "Area" in area else "d"
    fl_code = flight_level.replace("FL", "") if "FL" in flight_level else "340"
    if "SIGWX" in map_type.upper():
        url = f"https://aviationweather.gov/data/products/fax/F24_sigwx_hi_{area_code}.gif"
    else:
        url = f"https://aviationweather.gov/data/products/fax/F{forecast_hour}_wind_{fl_code}_{area_code}.gif"

    filename = f"{uuid.uuid4()}.gif"
    filepath = os.path.join(TEMP_MAP_DIR, filename)

    try:
        time.sleep(0.5)
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            with open(filepath, "wb") as f:
                f.write(response.content)
            return filepath
        return None
    except:
        return None


def fetch_tafs(airports: List[str]) -> str:
    if not airports:
        return "No alternative airports found."
    url = (
        f"https://aviationweather.gov/api/data/taf?ids={','.join(airports)}&format=raw"
    )
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200 and res.text.strip():
            return res.text
        return "TAF data not available from NOAA."
    except:
        return "Failed to fetch TAF data."


def fetch_hire_ascent() -> tuple:
    wind_str = "VRB05"
    temp_str = "-05"
    try:
        # Fetching for Katunayake (VCBI) 500hPa level (approx FL180/185)
        url = "https://api.open-meteo.com/v1/forecast?latitude=7.1803&longitude=79.8833&current=temperature_500hPa,wind_speed_500hPa,wind_direction_500hPa&wind_speed_unit=kn"
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            data = res.json().get("current", {})
            wd = data.get("wind_direction_500hPa")
            ws = data.get("wind_speed_500hPa")
            temp = data.get("temperature_500hPa")

            if wd is not None and ws is not None:
                wind_str = f"{int(wd):03d}{int(ws):02d}"
            if temp is not None:
                temp_int = int(temp)
                if temp_int < 0:
                    temp_str = f"-{abs(temp_int):02d}"
                else:
                    temp_str = f"+{abs(temp_int):02d}"
    except Exception as e:
        print("Error fetching HIRE ASCENT:", e)
    return wind_str, temp_str


def generate_briefing_pdf(
    filepath: str,
    req: FlightPlanRequest,
    duration_mins: int,
    arrival_time: datetime,
    forecasts: List[VerifiedForecast],
    taf_text: str,
):
    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=18,
    )
    styles = getSampleStyleSheet()
    title_style = styles["Heading1"]
    title_style.alignment = 1  # Center
    normal_style = styles["Normal"]

    elements = []
    temp_maps_to_delete = []

    # --- PAGE 1: COVER PAGE ---
    # Top Text
    elements.append(
        Paragraph(
            "<b>Serial No: - FF / 2023 / 11 / 02</b>",
            ParagraphStyle(name="Right", alignment=2, fontName="Helvetica-Bold"),
        )
    )
    elements.append(Spacer(1, 15))

    # Emblem
    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    emblem_img_path = os.path.join(backend_dir, "assets", "images", "emblem.png")
    if os.path.exists(emblem_img_path):
        try:
            img = RLImage(emblem_img_path, width=1.5 * inch, height=1.5 * inch)
            elements.append(img)
            elements.append(Spacer(1, 5))
        except:
            pass

    # Sinhala text (FM Font encoded)
    if os.path.exists(fm_font_path):
        sinhala_style = ParagraphStyle(
            name="Sinhala", fontName="FMSinhala", fontSize=24, alignment=1
        )
    else:
        sinhala_style = ParagraphStyle(name="SinhalaFallback", fontSize=24, alignment=1)
        
    raw_sinhala_text = "› ,xld ld<.=K úoHd fomd¾;fïka;=j"
    escaped_sinhala_text = raw_sinhala_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    elements.append(Paragraph(escaped_sinhala_text, sinhala_style))
    elements.append(Spacer(1, 15))
    elements.append(
        Paragraph(
            "DEPARTMENT OF METEOROLOGY, SRI LANKA",
            ParagraphStyle(
                name="EnTitle", fontName="Helvetica-Bold", fontSize=16, alignment=1
            ),
        )
    )
    elements.append(Spacer(1, 12))
    elements.append(
        Paragraph(
            "<b>METEOROLOGICAL CONDITIONS<br/>EN ROUTE<br/>and at<br/>AERODROMES</b>",
            ParagraphStyle(name="CenterNormal", alignment=1, fontSize=12, leading=14),
        )
    )
    elements.append(Spacer(1, 10))

    # Airplane
    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    airplane_img_path = os.path.join(backend_dir, "assets", "images", "airplane.png")
    if os.path.exists(airplane_img_path):
        try:
            # Reduced height to prevent spill to page 2
            img = RLImage(
                airplane_img_path, width=4 * inch, height=3 * inch, kind="proportional"
            )
            elements.append(img)
            elements.append(Spacer(1, 10))
        except:
            pass

    # Flight details
    flight_no = (
        req.flight_no
        if req.flight_no
        else (req.area.split("-")[0].strip() if "-" in req.area else "___")
    )
    flight_info = f"<b>Flight No. : &nbsp;&nbsp;&nbsp; <u><i>{flight_no}</i></u> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Route: {req.departure.upper()} - <u><i>{req.destination.upper()}</i></u></b>"
    elements.append(
        Paragraph(
            flight_info,
            ParagraphStyle(
                name="CenterLarge", alignment=1, fontSize=14, fontName="Helvetica-Bold"
            ),
        )
    )
    elements.append(Spacer(1, 15))

    elements.append(
        Paragraph(
            "<b>Issued by main Meteorological Office at Bandaranaike International Airport, Katunayake.</b>",
            ParagraphStyle(
                name="CenterSmall", alignment=1, fontSize=9, fontName="Helvetica-Bold"
            ),
        )
    )
    elements.append(Spacer(1, 5))
    issue_time = datetime.utcnow().strftime("%d %B %Y")

    elements.append(
        Paragraph(
            f"<b>Date: &nbsp;&nbsp; {issue_time}</b>",
            ParagraphStyle(
                name="DateLeft",
                alignment=0,
                fontSize=10,
                fontName="Helvetica-Bold",
                leftIndent=40,
            ),
        )
    )
    elements.append(Spacer(1, 20))

    elements.append(
        Paragraph(
            "<b>CGP</b>",
            ParagraphStyle(
                name="CenterBold14", alignment=1, fontSize=14, fontName="Helvetica-Bold"
            ),
        )
    )
    elements.append(Spacer(1, 5))
    elements.append(
        Paragraph(
            "................................................................",
            ParagraphStyle(name="CenterSmall", alignment=1, fontSize=10),
        )
    )
    elements.append(
        Paragraph(
            "<b>(Duty Meteorologist)</b>",
            ParagraphStyle(
                name="CenterSmall", alignment=1, fontSize=10, fontName="Helvetica-Bold"
            ),
        )
    )
    elements.append(Spacer(1, 20))

    # Take Off Data Table (Only the exact departure hour, i.e., the first forecast)
    elements.append(
        Paragraph(
            "<b>TAKE OFF DATA AT</b>",
            ParagraphStyle(
                name="CenterSmall", alignment=1, fontSize=10, fontName="Helvetica-Bold"
            ),
        )
    )
    elements.append(Spacer(1, 5))

    takeoff_fc = forecasts[0] if forecasts else None
    t_utc = (
        takeoff_fc.target_time.strftime("%H%M")
        if takeoff_fc and takeoff_fc.target_time
        else "-"
    )
    t_wind = f"VRB05"
    if (
        takeoff_fc
        and takeoff_fc.wind_dir is not None
        and takeoff_fc.wind_speed_kts is not None
    ):
        t_wind = f"{int(takeoff_fc.wind_dir):03d}{int(takeoff_fc.wind_speed_kts):02d}"

    t_temp = (
        f"{int(takeoff_fc.dry_temp_c)}"
        if takeoff_fc and takeoff_fc.dry_temp_c
        else "26"
    )
    t_qnh = (
        f"{int(takeoff_fc.qnh_hpa)}" if takeoff_fc and takeoff_fc.qnh_hpa else "1009"
    )

    table_data = [
        [
            Paragraph(
                "<b>TIME<br/>(UTC)</b>",
                ParagraphStyle(
                    name="c", alignment=1, fontSize=9, fontName="Helvetica-Bold"
                ),
            ),
            Paragraph(
                "<b>SURFACE WIND<br/>(KTS)</b>",
                ParagraphStyle(
                    name="c", alignment=1, fontSize=9, fontName="Helvetica-Bold"
                ),
            ),
            Paragraph(
                "<b>SURFACE TEMPERATURE<br/>(°C)</b>",
                ParagraphStyle(
                    name="c", alignment=1, fontSize=9, fontName="Helvetica-Bold"
                ),
            ),
            Paragraph(
                "<b>QNH<br/>(hPa)</b>",
                ParagraphStyle(
                    name="c", alignment=1, fontSize=9, fontName="Helvetica-Bold"
                ),
            ),
        ],
        [
            Paragraph(
                f"<font name='Courier-Bold' size=10>{t_utc}</font>",
                ParagraphStyle(name="c", alignment=1),
            ),
            Paragraph(
                f"<font name='Courier-Bold' size=10>{t_wind}</font>",
                ParagraphStyle(name="c", alignment=1),
            ),
            Paragraph(
                f"<font name='Courier-Bold' size=10>{t_temp}</font>",
                ParagraphStyle(name="c", alignment=1),
            ),
            Paragraph(
                f"<font name='Courier-Bold' size=10>{t_qnh}</font>",
                ParagraphStyle(name="c", alignment=1),
            ),
        ],
        ["", "", "", ""],
    ]
    t = Table(table_data, colWidths=[1 * inch, 2.2 * inch, 2.5 * inch, 1 * inch])
    t.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("INNERGRID", (0, 0), (-1, -1), 1, colors.black),
                ("BOX", (0, 0), (-1, -1), 1, colors.black),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    elements.append(t)
    elements.append(Spacer(1, 20))

    # HRI Ascent
    ha_wind, ha_temp = fetch_hire_ascent()

    elements.append(
        Paragraph(
            "<b>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; HRI &nbsp; ASCENT &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; (FL 185)</b>",
            ParagraphStyle(
                name="LeftBold",
                alignment=0,
                fontSize=10,
                fontName="Helvetica-Bold",
                leftIndent=150,
            ),
        )
    )
    elements.append(Spacer(1, 10))
    elements.append(
        Paragraph(
            f"<b>{ha_wind} &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; {ha_temp}</b>",
            ParagraphStyle(
                name="LeftBold",
                alignment=0,
                fontSize=11,
                fontName="Helvetica-Bold",
                leftIndent=100,
            ),
        )
    )
    elements.append(
        Paragraph(
            "<b>WIND .............................. KT &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; TEMP .............................. °C</b>",
            ParagraphStyle(
                name="LeftBold",
                alignment=0,
                fontSize=10,
                fontName="Helvetica-Bold",
                leftIndent=50,
            ),
        )
    )

    elements.append(PageBreak())

    # --- STATIC LEGEND TABLES (PAGES 2 & 3) ---
    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    legend_table1_path = os.path.join(backend_dir, "assets", "images", "legend_table1.png")
    legend_table2_path = os.path.join(backend_dir, "assets", "images", "legend_table2.png")

    if os.path.exists(legend_table1_path):
        try:
            elements.append(RLImage(legend_table1_path, width=7.4 * inch, height=10.5 * inch, kind="proportional"))
            elements.append(PageBreak())
        except Exception as e:
            print(f"Error loading legend_table1: {e}")

    if os.path.exists(legend_table2_path):
        try:
            elements.append(RLImage(legend_table2_path, width=7.4 * inch, height=10.5 * inch, kind="proportional"))
            elements.append(PageBreak())
        except Exception as e:
            print(f"Error loading legend_table2: {e}")

    # --- EXTENDED FORECAST & TAF ---
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

    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    emblem_img_path = os.path.join(backend_dir, "assets", "images", "emblem.png")
    emblem_flowable = ""
    if os.path.exists(emblem_img_path):
        try:
            emblem_flowable = RLImage(
                emblem_img_path, width=0.8 * inch, height=0.8 * inch
            )
        except:
            pass

    header_text = f"<b>DEPARTMENT OF METEOROLOGY – SRI LANKA</b><br/>{office_name}"
    contact_text = f"<b>Tp:</b> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; {contact_tp}<br/><b>Fax:</b> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; {contact_fax}<br/><b>E-mail:</b> &nbsp;&nbsp; {contact_email}"

    header_table = Table(
        [
            [
                emblem_flowable,
                Paragraph(
                    header_text, ParagraphStyle(name="H", fontSize=10, leading=14)
                ),
                Paragraph(
                    contact_text, ParagraphStyle(name="C", fontSize=8, leading=12)
                ),
            ]
        ],
        colWidths=[1 * inch, 4 * inch, 2.5 * inch],
    )
    header_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LINEBELOW", (0, 0), (-1, -1), 1, colors.black),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    elements.append(header_table)
    elements.append(Spacer(1, 10))

    flight_no = req.area.split("-")[0].strip() if "-" in req.area else "___"
    flight_reg_text = f"<b>FLIGHT REGISTRATION NO &nbsp;&nbsp;&nbsp; : &nbsp;&nbsp; {flight_no}</b><br/><b>DESTINATION &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; : &nbsp;&nbsp; {req.destination.upper()}</b>"
    elements.append(
        Paragraph(
            flight_reg_text,
            ParagraphStyle(
                name="Mono10", fontName="Courier-Bold", fontSize=10, leading=14
            ),
        )
    )
    elements.append(Spacer(1, 15))

    elements.append(
        Paragraph(
            f"<u><b>EXTENDED WEATHER FORECAST FOR TAKE-OFF</b></u>",
            ParagraphStyle(
                name="CH", alignment=1, fontSize=11, fontName="Helvetica-Bold"
            ),
        )
    )
    elements.append(
        Paragraph(
            airport_name_full, ParagraphStyle(name="CN", alignment=1, fontSize=10)
        )
    )
    issue_time_str = datetime.utcnow().strftime("%H%M UTC %d %B %Y")
    elements.append(
        Paragraph(
            f"<b>Issued Time</b> - {issue_time_str}",
            ParagraphStyle(name="CN", alignment=1, fontSize=10),
        )
    )
    elements.append(Spacer(1, 10))

    ext_table_data = [
        [
            Paragraph(
                "<b>Time<br/>(hour)</b>",
                ParagraphStyle(name="c", alignment=1, fontSize=9),
            ),
            "",
            Paragraph(
                "<b>Wind<br/>(deg/kt)</b>",
                ParagraphStyle(name="c", alignment=1, fontSize=9),
            ),
            Paragraph(
                "<b>Air Temp<br/>(deg C)</b>",
                ParagraphStyle(name="c", alignment=1, fontSize=9),
            ),
            Paragraph(
                "<b>QNH<br/>(hPa)</b>",
                ParagraphStyle(name="c", alignment=1, fontSize=9),
            ),
            Paragraph(
                "<b>Remarks</b>", ParagraphStyle(name="c", alignment=1, fontSize=9)
            ),
        ],
        [
            Paragraph("SLST", ParagraphStyle(name="c", alignment=1, fontSize=9)),
            Paragraph("UTC", ParagraphStyle(name="c", alignment=1, fontSize=9)),
            "",
            "",
            "",
            "",
        ],
    ]

    for fc in forecasts:
        utc_time = fc.target_time.strftime("%H%M") if fc.target_time else "-"
        slst_time = (
            (fc.target_time + timedelta(hours=5, minutes=30)).strftime("%H%M")
            if fc.target_time
            else "-"
        )
        wind_str = "VRB05"
        if fc.wind_speed_kts is not None and fc.wind_dir is not None:
            wind_str = f"{int(fc.wind_dir):03d}{int(fc.wind_speed_kts):02d}"

        temp_str = f"{int(fc.dry_temp_c)}" if fc.dry_temp_c is not None else "-"
        qnh_str = f"{int(fc.qnh_hpa)}" if fc.qnh_hpa is not None else "-"
        remarks = fc.remarks if fc.remarks else (fc.clouds if fc.clouds else "-")

        ext_table_data.append(
            [
                Paragraph(
                    slst_time,
                    ParagraphStyle(
                        name="c", alignment=1, fontSize=10, fontName="Courier"
                    ),
                ),
                Paragraph(
                    utc_time,
                    ParagraphStyle(
                        name="c", alignment=1, fontSize=10, fontName="Courier"
                    ),
                ),
                Paragraph(
                    f"<b>{wind_str}</b>",
                    ParagraphStyle(
                        name="c", alignment=1, fontSize=10, fontName="Helvetica-Bold"
                    ),
                ),
                Paragraph(
                    f"<b>{temp_str}</b>",
                    ParagraphStyle(
                        name="c", alignment=1, fontSize=10, fontName="Helvetica-Bold"
                    ),
                ),
                Paragraph(
                    f"<b>{qnh_str}</b>",
                    ParagraphStyle(
                        name="c", alignment=1, fontSize=10, fontName="Helvetica-Bold"
                    ),
                ),
                Paragraph(
                    f"<b>{remarks}</b>",
                    ParagraphStyle(
                        name="c", alignment=1, fontSize=10, fontName="Helvetica-Bold"
                    ),
                ),
            ]
        )

    t3 = Table(
        ext_table_data,
        colWidths=[1 * inch, 1 * inch, 1.8 * inch, 1.2 * inch, 1 * inch, 1.5 * inch],
    )
    t3.setStyle(
        TableStyle(
            [
                ("SPAN", (0, 0), (1, 0)),
                ("SPAN", (2, 0), (2, 1)),
                ("SPAN", (3, 0), (3, 1)),
                ("SPAN", (4, 0), (4, 1)),
                ("SPAN", (5, 0), (5, 1)),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("INNERGRID", (0, 0), (-1, -1), 1, colors.black),
                ("BOX", (0, 0), (-1, -1), 1, colors.black),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    elements.append(t3)
    elements.append(Spacer(1, 10))
    elements.append(
        Paragraph(
            "<b>Note:</b> This forecast may be amended at any time. For clarification of meteorological issues, please contact Duty Meteorologist.",
            ParagraphStyle(name="SmallMono", fontSize=8, fontName="Courier"),
        )
    )
    elements.append(Spacer(1, 15))

    elements.append(
        Paragraph(
            "<u><b>TAF & METAR BULLETIN</b></u>",
            ParagraphStyle(
                name="CH", alignment=1, fontSize=11, fontName="Helvetica-Bold"
            ),
        )
    )
    elements.append(Spacer(1, 5))

    # 2-column TAF layout (Multi-row for safe pagination)
    import re

    taf_blocks = re.split(r"(?=TAF )", taf_text)
    taf_blocks = [b.strip() for b in taf_blocks if b.strip()]

    half = (len(taf_blocks) + 1) // 2
    left_blocks = taf_blocks[:half]
    right_blocks = taf_blocks[half:]

    taf_style = ParagraphStyle(name="Taf", fontName="Courier", fontSize=8, leading=10)
    taf_rows = []

    for i in range(half):
        left_p = (
            Paragraph(left_blocks[i].replace("\n", "<br/>"), taf_style)
            if i < len(left_blocks)
            else Paragraph("", taf_style)
        )
        right_p = (
            Paragraph(right_blocks[i].replace("\n", "<br/>"), taf_style)
            if i < len(right_blocks)
            else Paragraph("", taf_style)
        )
        taf_rows.append([left_p, right_p])

    if not taf_rows:
        taf_rows.append([Paragraph("No TAF Data", taf_style), Paragraph("", taf_style)])

    taf_table = Table(taf_rows, colWidths=[3.75 * inch, 3.75 * inch])
    taf_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                (
                    "BOX",
                    (0, 0),
                    (0, -1),
                    1,
                    colors.black,
                ),  # Border around col 1 continuously
                (
                    "BOX",
                    (1, 0),
                    (1, -1),
                    1,
                    colors.black,
                ),  # Border around col 2 continuously
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    elements.append(taf_table)
    elements.append(PageBreak())

    # --- MAPS SECTION ---
    dep_time_str = datetime.fromisoformat(req.departure_time).strftime(
        "%d-%b-%Y %H:%M Z"
    )
    arr_time_str = arrival_time.strftime("%d-%b-%Y %H:%M Z")
    flight_schedule_str = f"Flight Schedule: {dep_time_str} TO {arr_time_str}"

    base_dt = get_noaa_model_base_time()
    dep_dt_val = datetime.fromisoformat(req.departure_time).replace(tzinfo=None)
    forecast_hours = get_forecast_lead_times(dep_dt_val, duration_mins, base_dt)

    has_wind_temp = any("WIND" in m.upper() for m in req.maps)
    has_sigwx = any("SIGWX" in m.upper() for m in req.maps)

    # 1. Upper Wind & Temperature Charts (Iterate through Flight Levels & Forecast Lead Times)
    if has_wind_temp:
        for fl in req.flight_levels:
            for fh in forecast_hours:
                chart_valid_dt = base_dt + timedelta(hours=int(fh))
                valid_win_start = chart_valid_dt - timedelta(hours=3)
                valid_win_end = chart_valid_dt + timedelta(hours=3)
                chart_valid_str = f"VALID: {chart_valid_dt.strftime('%d-%b %H:%M Z')} (Window: {valid_win_start.strftime('%H:%MZ')} - {valid_win_end.strftime('%H:%MZ')})"

                stage_suffix = f" (T+{fh}H Forecast)"
                if len(forecast_hours) > 1:
                    if fh == forecast_hours[0]:
                        stage_suffix += " [Departure / En-route Stage]"
                    elif fh == forecast_hours[-1]:
                        stage_suffix += " [Descent / Arrival Stage]"
                    else:
                        stage_suffix += " [Mid En-route Stage]"

                elements.append(
                    Paragraph(
                        f"Flight Level: {fl} — Upper Wind &amp; Temperature{stage_suffix}",
                        styles["Heading3"],
                    )
                )
                elements.append(Spacer(1, 10))

                map_filepath = get_live_map("WIND", fl, req.area, fh)
                header_caption = f"Upper Wind &amp; Temp Chart{stage_suffix} - {fl} | {chart_valid_str} | {flight_schedule_str}"

                if map_filepath and os.path.exists(map_filepath):
                    temp_maps_to_delete.append(map_filepath)
                    try:
                        img = RLImage(
                            map_filepath,
                            width=7.2 * inch,
                            height=7 * inch,
                            kind="proportional",
                        )
                        box_data = [
                            [
                                Paragraph(
                                    f"<b>{header_caption}</b>",
                                    ParagraphStyle(
                                        name="MH",
                                        alignment=1,
                                        fontSize=8,
                                        leading=10,
                                    ),
                                )
                            ],
                            [img],
                        ]
                    except:
                        box_data = [
                            [
                                f"Upper Wind & Temp Chart{stage_suffix} - {fl}\n\n{chart_valid_str}\n\n[ ERROR LOADING MAP IMAGE ]"
                            ]
                        ]
                else:
                    box_data = [
                        [
                            f"Upper Wind & Temp Chart{stage_suffix} - {fl}\n\n{chart_valid_str}\n\n[ MAP FETCH TIMEOUT / NOT AVAILABLE ]"
                        ]
                    ]

                box_table = Table(box_data, colWidths=[7.2 * inch])
                box_table.setStyle(
                    TableStyle(
                        [
                            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                            ("BACKGROUND", (0, 0), (-1, -1), colors.whitesmoke),
                            ("GRID", (0, 0), (-1, -1), 1, colors.grey),
                        ]
                    )
                )
                elements.append(box_table)
                elements.append(PageBreak())

    # 2. Significant Weather Chart (SIGWX High-Level FL250–FL630) — Generated ONCE for entire flight
    if has_sigwx:
        sigwx_valid_dt = base_dt + timedelta(hours=24)
        sigwx_valid_str = f"T+24H Forecast Valid: {sigwx_valid_dt.strftime('%d-%b-%Y %H:%M Z')}"
        area_name = req.area.upper() if req.area else "AREA D"

        elements.append(
            Paragraph(
                f"Significant Weather (High-Level SIGWX: FL250 – FL630) — {area_name}",
                styles["Heading3"],
            )
        )
        elements.append(Spacer(1, 10))

        map_filepath = get_live_map("SIGWX", "340", req.area, "24")
        sigwx_caption = f"ICAO {area_name} SIGWX Chart (High-Level: FL250–FL630) | {sigwx_valid_str} | {flight_schedule_str}"

        if map_filepath and os.path.exists(map_filepath):
            temp_maps_to_delete.append(map_filepath)
            try:
                img = RLImage(
                    map_filepath,
                    width=7.2 * inch,
                    height=7 * inch,
                    kind="proportional",
                )
                box_data = [
                    [
                        Paragraph(
                            f"<b>{sigwx_caption}</b>",
                            ParagraphStyle(
                                name="SH",
                                alignment=1,
                                fontSize=8,
                                leading=10,
                            ),
                        )
                    ],
                    [img],
                ]
            except:
                box_data = [
                    [
                        f"ICAO {area_name} SIGWX Chart\n\n{sigwx_valid_str}\n\n[ ERROR LOADING MAP IMAGE ]"
                    ]
                ]
        else:
            box_data = [
                [
                    f"ICAO {area_name} SIGWX Chart\n\n{sigwx_valid_str}\n\n[ MAP FETCH TIMEOUT / NOT AVAILABLE ]"
                ]
            ]

        box_table = Table(box_data, colWidths=[7.2 * inch])
        box_table.setStyle(
            TableStyle(
                [
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("BACKGROUND", (0, 0), (-1, -1), colors.whitesmoke),
                    ("GRID", (0, 0), (-1, -1), 1, colors.grey),
                ]
            )
        )
        elements.append(box_table)
        elements.append(PageBreak())

    # --- BEFORE LAST PAGE (SIGNIFICANT WEATHER / CHART SYMBOLS) ---
    before_last_path = os.path.join(backend_dir, "assets", "images", "befor last page.png")
    if os.path.exists(before_last_path):
        try:
            elements.append(
                RLImage(
                    before_last_path,
                    width=7.4 * inch,
                    height=10.5 * inch,
                    kind="proportional",
                )
            )
            elements.append(PageBreak())
        except Exception as e:
            print(f"Error loading before last page: {e}")

    # --- LAST PAGE (LOCATION INDICATORS / DOC CLOSING) ---
    last_page_path = os.path.join(backend_dir, "assets", "images", "lastpage.png")
    if os.path.exists(last_page_path):
        try:
            elements.append(
                RLImage(
                    last_page_path,
                    width=7.4 * inch,
                    height=10.5 * inch,
                    kind="proportional",
                )
            )
            # No need for PageBreak() on the absolute last page
        except Exception as e:
            print(f"Error loading last page: {e}")

    doc.build(elements, onFirstPage=draw_page_border)

    # Clean up temporary map files downloaded for this PDF
    for tm in temp_maps_to_delete:
        try:
            if os.path.exists(tm):
                os.remove(tm)
        except Exception:
            pass


@router.post("/flight-plan")
def create_flight_plan(req: FlightPlanRequest, db: Session = Depends(get_db)):
    try:
        # Parse datetime and make naive
        dep_dt = datetime.fromisoformat(req.departure_time).replace(tzinfo=None)

        # TIME LOGIC: Departure Time up to +3 hours (to get 3 hourly records)
        end_dt = dep_dt + timedelta(hours=3)
        forecasts = (
            db.query(VerifiedForecast)
            .filter(
                VerifiedForecast.target_time >= dep_dt - timedelta(minutes=30),
                VerifiedForecast.target_time <= end_dt,
            )
            .order_by(VerifiedForecast.target_time.asc())
            .limit(3)
            .all()
        )

        if not forecasts:
            # Fallback
            fallback = (
                db.query(VerifiedForecast)
                .filter(
                    VerifiedForecast.target_time >= dep_dt - timedelta(hours=6),
                    VerifiedForecast.target_time <= dep_dt + timedelta(hours=6),
                )
                .order_by(VerifiedForecast.target_time.asc())
                .limit(3)
                .all()
            )

            if not fallback:
                recent_fallback = (
                    db.query(VerifiedForecast)
                    .order_by(VerifiedForecast.target_time.desc())
                    .limit(3)
                    .all()
                )
                if recent_fallback:
                    forecasts = list(reversed(recent_fallback))
                else:
                    raise HTTPException(
                        status_code=400,
                        detail=f"No verified meteorological forecast data available for the requested timeframe ({dep_dt.strftime('%Y-%m-%d %H:%M Z')}).",
                    )
            else:
                forecasts = fallback

        dest_upper = req.destination.upper()
        flight_record = (
            db.query(FlightTimeAndFlights)
            .filter(FlightTimeAndFlights.destination == dest_upper)
            .first()
        )
        duration_mins = (
            flight_record.time_period_mins
            if flight_record and flight_record.time_period_mins
            else 240
        )
        arrival_dt = dep_dt + timedelta(minutes=duration_mins)

        # Find matching route alternatives
        matching_route = (
            db.query(RouteAlternatives)
            .filter(RouteAlternatives.airports.like(f"%{dest_upper}%"))
            .first()
        )
        airports_list = []
        if matching_route:
            airports_list = matching_route.airports.split()
        else:
            # Fallback just use the destination and departure
            airports_list = [req.departure.upper(), dest_upper]

        taf_text = fetch_tafs(airports_list)

        doc_id = str(uuid.uuid4())
        pilot_ref = req.pilot_reference if req.pilot_reference else "guest"
        safe_pilot_ref = "".join([c for c in pilot_ref if c.isalnum() or c in ('-', '_')])
        
        # If we are confirming a preview, just rename it
        if not req.preview_only and req.preview_url:
            preview_filename = req.preview_url.split("/")[-1]
            old_filepath = os.path.join(DOCS_DIR, preview_filename)
            if os.path.exists(old_filepath):
                filename = preview_filename.replace("preview_", "briefing_", 1)
                filepath = os.path.join(DOCS_DIR, filename)
                os.rename(old_filepath, filepath)
            else:
                raise HTTPException(status_code=404, detail="Preview document not found or expired.")
        else:
            # Clean up any preview files for this pilot when they generate a real one
            if not req.preview_only:
                if os.path.exists(DOCS_DIR):
                    for f in os.listdir(DOCS_DIR):
                        if f.startswith(f"preview_{safe_pilot_ref}_") and f.endswith(".pdf"):
                            try:
                                os.remove(os.path.join(DOCS_DIR, f))
                            except Exception:
                                pass
    
            prefix = "preview" if req.preview_only else "briefing"
            filename = f"{prefix}_{safe_pilot_ref}_{req.departure.upper()}_{req.destination.upper()}_{doc_id}.pdf"
            filepath = os.path.join(DOCS_DIR, filename)
    
            generate_briefing_pdf(
                filepath, req, duration_mins, arrival_dt, forecasts, taf_text
            )

        log_entry = SystemLogs(
            level="info",
            component=f"Pilot_{req.departure.upper()}_{req.destination.upper()}",
            message="Flight Briefing Document Generated",
            details=json.dumps(
                {
                    "departure": req.departure.upper(),
                    "destination": req.destination.upper(),
                    "document_url": f"/documents/{filename}",
                }
            ),
        )
        db.add(log_entry)
        db.commit()

        # Save to PilotFlightPlan history ONLY if not previewing
        if not req.preview_only:
            try:
                new_plan = PilotFlightPlan(
                    pilot_reference=req.pilot_reference,
                    flight_no=req.flight_no,
                    departure=req.departure,
                    destination=req.destination,
                    departure_time=dep_dt,
                    duration_mins=duration_mins,
                )
                db.add(new_plan)
                db.commit()
                db.refresh(new_plan)
            except Exception as e:
                import traceback

                error_trace = traceback.format_exc()
                print(f"Error saving to PilotFlightPlan history: {e}")
                with open("save_error.log", "w") as f:
                    f.write(error_trace)
                db.rollback()

        return {
            "message": "Flight plan successfully generated",
            "document_url": f"http://localhost:8000/documents/{filename}",
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/last-flight-plan")
def get_last_flight_plan(pilot_reference: str, db: Session = Depends(get_db)):
    plan = (
        db.query(PilotFlightPlan)
        .filter(PilotFlightPlan.pilot_reference == pilot_reference)
        .order_by(PilotFlightPlan.created_at.desc())
        .first()
    )
    if plan:
        return plan
    return {}


@router.get("/flight-plans")
def get_flight_plans(pilot_reference: str, db: Session = Depends(get_db)):
    plans = (
        db.query(PilotFlightPlan)
        .filter(PilotFlightPlan.pilot_reference == pilot_reference)
        .order_by(PilotFlightPlan.created_at.desc())
        .limit(50)
        .all()
    )
    return plans


@router.get("/next-flight")
def get_next_flight(db: Session = Depends(get_db)):
    now_local = datetime.utcnow() + timedelta(hours=5, minutes=30)
    current_hm = now_local.strftime("%H:%M")

    flights = (
        db.query(FlightTimeAndFlights)
        .filter(FlightTimeAndFlights.departure_time_local != None)
        .all()
    )

    upcoming_flights = []
    for f in flights:
        if f.departure_time_local and ":" in f.departure_time_local:
            if f.departure_time_local >= current_hm:
                upcoming_flights.append(f)

    if upcoming_flights:
        upcoming_flights.sort(key=lambda x: x.departure_time_local)
        next_flight = upcoming_flights[0]
    else:
        valid_flights = [
            f
            for f in flights
            if f.departure_time_local and ":" in f.departure_time_local
        ]
        if valid_flights:
            valid_flights.sort(key=lambda x: x.departure_time_local)
            next_flight = valid_flights[0]
        else:
            return {}

    return {
        "flight_no": next_flight.flight,
        "destination": next_flight.destination,
        "departure_time_local": next_flight.departure_time_local,
        "duration_mins": next_flight.time_period_mins,
    }


@router.get("/flight-info")
def get_flight_info_by_dest(destination: str, db: Session = Depends(get_db)):
    if not destination or len(destination) < 3:
        return {}

    dest_upper = destination.upper()
    flight = (
        db.query(FlightTimeAndFlights)
        .filter(FlightTimeAndFlights.destination == dest_upper)
        .first()
    )

    if flight:
        return {
            "flight_no": flight.flight,
            "departure_time_local": flight.departure_time_local,
            "duration_mins": flight.time_period_mins,
        }
    return {}


@router.get("/flight-info-by-time")
def get_flight_info_by_time(time_local: str, db: Session = Depends(get_db)):
    if not time_local:
        return {}

    flight = (
        db.query(FlightTimeAndFlights)
        .filter(FlightTimeAndFlights.departure_time_local == time_local)
        .first()
    )

    if flight:
        return {
            "flight_no": flight.flight,
            "destination": flight.destination,
            "departure_time_local": flight.departure_time_local,
            "duration_mins": flight.time_period_mins,
        }
    return {}

@router.get("/my-documents")
def get_my_documents(pilot_reference: str):
    if not pilot_reference:
        return []
        
    safe_pilot_ref = "".join([c for c in pilot_reference if c.isalnum() or c in ('-', '_')])
    prefix = f"briefing_{safe_pilot_ref}_"
    
    docs = []
    if os.path.exists(DOCS_DIR):
        for f in os.listdir(DOCS_DIR):
            if f.startswith(prefix) and f.endswith(".pdf"):
                filepath = os.path.join(DOCS_DIR, f)
                created_time = datetime.fromtimestamp(os.path.getctime(filepath))
                
                # Parse departure and destination from filename: briefing_ref_DEP_DEST_uuid.pdf
                parts = f.replace(".pdf", "").split("_")
                
                departure = "Unknown"
                destination = "Unknown"
                if len(parts) >= 5:
                    departure = parts[2]
                    destination = parts[3]
                
                # Status logic: Valid for 12 hours after creation
                now = datetime.now()
                is_expired = now > (created_time + timedelta(hours=12))
                status_val = "Expired" if is_expired else "Valid"
                
                docs.append({
                    "reference": f.replace(".pdf", ""),
                    "route": f"{departure} → {destination}",
                    "forecastDate": created_time.strftime("%d %b %Y %H:%M"),
                    "status": status_val,
                    "url": f"http://localhost:8000/documents/{f}"
                })
                
    docs.sort(key=lambda x: os.path.getctime(os.path.join(DOCS_DIR, f"{x['reference']}.pdf")), reverse=True)
    return docs
