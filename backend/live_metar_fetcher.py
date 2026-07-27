import os
import sys
import requests
import re
from datetime import datetime
from sqlalchemy.orm import Session

# Ensure we can import backend modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from backend.data.database import SessionLocal, engine, Base
from backend.data.models import WeatherData, SystemLogs

API_URL = "https://aviationweather.gov/api/data/metar?ids=VCBI&format=json"

def log_event(db_session, level, component, message, details=None):
    try:
        log = SystemLogs(level=level, component=component, message=message, details=details)
        db_session.add(log)
        db_session.commit()
    except Exception as e:
        print(f"Failed to write log to DB: {e}")
    print(f"[{level}] {component}: {message}")

def calculate_rh(temp, dewp):
    if temp is None or dewp is None:
        return None
    # Magnus-Tetens approximation
    e = 6.11 * (10 ** (7.5 * temp / (237.3 + temp)))
    es = 6.11 * (10 ** (7.5 * dewp / (237.3 + dewp)))
    return round((es / e) * 100, 2)

def extract_visibility_from_raw(raw_ob):
    """
    Extracts visibility (e.g., 9999) from raw METAR.
    It usually follows the wind group (e.g., 22012KT).
    """
    # Regex to find KT followed by space and then digits
    match = re.search(r'KT\s+(\d{4})', raw_ob)
    if match:
        return float(match.group(1))
    return 9999.0 # fallback

def extract_weather_and_clouds(raw_ob):
    """
    Extracts clouds (like FEW018) and weather phenomena (like RA, HZ).
    """
    parts = raw_ob.split(' ')
    clouds = []
    weather = []
    
    # Common cloud and weather prefixes
    cloud_prefixes = ('FEW', 'SCT', 'BKN', 'OVC', 'NSC', 'CAVOK', 'SKC')
    weather_codes = ('RA', 'HZ', 'BR', 'FG', 'TS', 'DZ', 'VCTS', 'SHRA')
    
    for part in parts:
        if part.startswith(cloud_prefixes):
            clouds.append(part)
        elif any(w in part for w in weather_codes) and not part.startswith(cloud_prefixes):
            if part not in ('NOSIG', 'METAR', 'VCBI') and not re.match(r'\d{6}Z', part) and not part.endswith('KT') and '/' not in part:
                weather.append(part)
                
    return (
        " ".join(clouds) if clouds else "NSC", 
        " ".join(weather) if weather else None
    )

def fetch_and_store_live_metar():
    print(f"[{datetime.utcnow()}] Fetching live METAR data for VCBI...")
    
    # Initialize DB first so we can log errors
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    try:
        response = requests.get(API_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if not data or len(data) == 0:
            log_event(db, "WARNING", "Live_METAR_Fetcher", "No data returned from API.")
            return
            
        records_added = 0
        for ob in reversed(data): # Process oldest to newest
            raw_ob = ob.get('rawOb', '')
            
            report_time_str = ob.get('reportTime')
            if not report_time_str:
                continue
                
            dt = datetime.strptime(report_time_str, "%Y-%m-%dT%H:%M:%S.000Z")
            
            year = dt.year
            month = dt.month
            date = dt.day
            time_utc = dt.strftime("%H%M")
            
            # Check if this record already exists (to prevent duplicates)
            existing = db.query(WeatherData).filter_by(
                year=year, month=month, date=date, time_utc=time_utc
            ).first()
            
            if existing:
                continue # Skip if already in DB
                
            wind_dir = float(ob.get('wdir')) if ob.get('wdir') is not None else None
            wind_speed_kts = float(ob.get('wspd')) if ob.get('wspd') is not None else None
            dry_temp_c = float(ob.get('temp')) if ob.get('temp') is not None else None
            dew_point_c = float(ob.get('dewp')) if ob.get('dewp') is not None else None
            qnh_hpa = float(ob.get('altim')) if ob.get('altim') is not None else None
            
            rh_percent = calculate_rh(dry_temp_c, dew_point_c)
            visibility = extract_visibility_from_raw(raw_ob)
            clouds, weather = extract_weather_and_clouds(raw_ob)
            
            new_record = WeatherData(
                timestamp_utc=datetime.utcnow(),
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
                qnh_hpa=qnh_hpa
            )
            db.add(new_record)
            records_added += 1
            
        db.commit()
        
        if records_added > 0:
            log_event(db, "SUCCESS", "Live_METAR_Fetcher", f"Added {records_added} new live METAR record(s).")
        else:
            log_event(db, "INFO", "Live_METAR_Fetcher", "No new METAR records. All fetched data already exists in DB.")
            
    except Exception as e:
        log_event(db, "ERROR", "Live_METAR_Fetcher", f"Error fetching live METAR: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    fetch_and_store_live_metar()
