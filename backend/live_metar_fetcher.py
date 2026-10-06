import os
import sys
import requests
import math
import re
from datetime import datetime
from sqlalchemy.orm import Session

# Ensure we can import backend modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from backend.data.database import SessionLocal, engine, Base
from backend.data.models import WeatherData, SystemLogs

API_URL = "https://aviationweather.gov/api/data/metar?ids=VCBI&format=json"


def log_event(db_session, level, component, message, details=None):
    try:
        log = SystemLogs(
            level=level, component=component, message=message, details=details
        )
        db_session.add(log)
        db_session.commit()
    except Exception as e:
        print(f"Failed to write log to DB: {e}")
    print(f"[{level}] {component}: {message}")


def calculate_rh(temp, dewp):
    """
    Calculates Relative Humidity (%) using the Magnus-Tetens formula.
    """
    if temp is None or dewp is None:
        return None
    try:
        beta = (17.625 * dewp) / (243.04 + dewp)
        alpha = (17.625 * temp) / (243.04 + temp)
        rh = 100 * math.exp(beta - alpha)
        return round(rh, 2)
    except Exception:
        return None


def extract_visibility_from_raw(raw_ob):
    """
    Extracts visibility (e.g., 9999) from raw METAR.
    It usually follows the wind group (e.g., 22012KT).
    """
    match = re.search(r"KT\s+(\d{4})", raw_ob)
    if match:
        return float(match.group(1))
    return 9999.0  # fallback


def extract_weather_and_clouds(raw_ob):
    """
    Extracts clouds (like FEW018) and weather phenomena (like RA, HZ).
    """
    parts = raw_ob.split(" ")
    clouds = []
    weather = []

    cloud_prefixes = ("FEW", "SCT", "BKN", "OVC", "NSC", "CAVOK", "SKC")
    weather_codes = ("RA", "HZ", "BR", "FG", "TS", "DZ", "VCTS", "SHRA")

    for part in parts:
        if part.startswith(cloud_prefixes):
            clouds.append(part)
        elif any(w in part for w in weather_codes) and not part.startswith(
            cloud_prefixes
        ):
            if (
                part not in ("NOSIG", "METAR", "VCBI")
                and not re.match(r"\d{6}Z", part)
                and not part.endswith("KT")
                and "/" not in part
            ):
                weather.append(part)

    return (
        " ".join(clouds) if clouds else "NSC",
        " ".join(weather) if weather else None,
    )


def parse_metar_time(time_str):
    if not time_str:
        return datetime.utcnow()
    for fmt in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(time_str, fmt)
        except ValueError:
            pass
    try:
        from dateutil import parser

        return parser.parse(time_str).replace(tzinfo=None)
    except Exception:
        return datetime.utcnow()


def safe_float(val):
    if val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def fetch_and_store_live_metar(hours=None):
    """
    Fetches METAR data from AviationWeather API for VCBI.
    Automatically detects time gap since last database record (up to 48 hours)
    so no data is lost even if the laptop was asleep or offline!
    """
    # Initialize DB first so we can log errors
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Auto-detect gap since last observation if hours is not specified
    if hours is None:
        try:
            last_rec = (
                db.query(WeatherData).order_by(WeatherData.timestamp_utc.desc()).first()
            )
            if last_rec and last_rec.timestamp_utc:
                gap_hours = (
                    datetime.utcnow() - last_rec.timestamp_utc
                ).total_seconds() / 3600.0
                hours = max(2, min(48, math.ceil(gap_hours + 2)))
            else:
                hours = 24
        except Exception:
            hours = 24

    print(f"[{datetime.now()}] Fetching METAR data for VCBI (Last {hours} hours)...")
    url = (
        f"https://aviationweather.gov/api/data/metar?ids=VCBI&format=json&hours={hours}"
    )
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()

        if not response.text or not response.text.strip():
            log_event(
                db,
                "WARNING",
                f"Live_METAR_Fetcher_{hours}H",
                "Empty response from AviationWeather API.",
            )
            return 0

        try:
            data = response.json()
        except Exception as json_err:
            log_event(
                db,
                "WARNING",
                f"Live_METAR_Fetcher_{hours}H",
                f"Non-JSON response from API: {json_err}",
            )
            return 0

        if not data or len(data) == 0:
            log_event(
                db,
                "WARNING",
                f"Live_METAR_Fetcher_{hours}H",
                "No data returned from API.",
            )
            return 0

        records_added = 0
        for ob in reversed(data):  # Process oldest to newest
            raw_ob = ob.get("rawOb", "")

            report_time_str = ob.get("reportTime")
            if not report_time_str:
                continue

            dt = datetime.strptime(report_time_str, "%Y-%m-%dT%H:%M:%S.000Z")

            year = dt.year
            month = dt.month
            date = dt.day
            time_utc = dt.strftime("%H%M")

            # Check if this record already exists (to prevent duplicates)
            existing = (
                db.query(WeatherData)
                .filter_by(year=year, month=month, date=date, time_utc=time_utc)
                .first()
            )

            if existing:
                continue  # Skip if already in DB

            wind_dir = safe_float(ob.get("wdir"))
            wind_speed_kts = safe_float(ob.get("wspd"))
            dry_temp_c = safe_float(ob.get("temp"))
            dew_point_c = safe_float(ob.get("dewp"))
            qnh_hpa = safe_float(ob.get("altim"))

            rh_percent = calculate_rh(dry_temp_c, dew_point_c)
            visibility = extract_visibility_from_raw(raw_ob)
            clouds, weather = extract_weather_and_clouds(raw_ob)

            new_record = WeatherData(
                timestamp_utc=dt,
                year=year,
                month=month,
                date=date,
                time_utc=time_utc,
                wind_dir=wind_dir,
                wind_speed_kts=wind_speed_kts,
                visibility=visibility,
                weather=weather,
                clouds=clouds,
                dry_temp_c=dry_temp_c,
                dew_point_c=dew_point_c,
                rh_percent=rh_percent,
                qnh_hpa=qnh_hpa,
            )
            db.add(new_record)
            records_added += 1

        db.commit()
        if records_added > 0:
            log_event(
                db,
                "SUCCESS",
                f"Live_METAR_Fetcher_{hours}H",
                f"Added {records_added} new live METAR record(s).",
            )
        else:
            log_event(
                db,
                "INFO",
                f"Live_METAR_Fetcher_{hours}H",
                "No new METAR records. All fetched data already exists in DB.",
            )

        return records_added
    except Exception as e:
        log_event(
            db,
            "ERROR",
            f"Live_METAR_Fetcher_{hours}H",
            f"Error fetching live METAR: {str(e)}",
        )
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    fetch_and_store_live_metar(hours=2)


# z