import requests
import math
from datetime import datetime
import os
import sys

# Ensure backend modules can be imported if run directly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from backend.data.database import SessionLocal
from backend.data.models import WeatherData

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

def fetch_and_store_live_metar(hours=None):
    """
    Fetches METAR data from AviationWeather API for VCBI.
    Automatically detects time gap since last database record (up to 48 hours)
    so no data is lost even if the laptop was asleep or offline!
    """
    db = SessionLocal()
    
    # Auto-detect gap since last observation if hours is not specified
    if hours is None:
        try:
            last_rec = db.query(WeatherData).order_by(WeatherData.timestamp_utc.desc()).first()
            if last_rec and last_rec.timestamp_utc:
                gap_hours = (datetime.utcnow() - last_rec.timestamp_utc).total_seconds() / 3600.0
                hours = max(2, min(48, math.ceil(gap_hours + 2)))
            else:
                hours = 24
        except Exception:
            hours = 24
            
    print(f"[{datetime.now()}] Fetching METAR data for the past {hours} hours (Auto-Backfill)...")
    url = f"https://aviationweather.gov/api/data/metar?ids=VCBI&format=json&hours={hours}"
    
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"[{datetime.now()}] Error fetching live METAR data: {e}")
        db.close()
        return 0

    records_added = 0

    try:
        for obs in data:
            report_time_str = obs.get("reportTime") or obs.get("receiptTime")
            if not report_time_str:
                continue
                
            obs_dt = parse_metar_time(report_time_str)
            
            year = obs_dt.year
            month = obs_dt.month
            date = obs_dt.day
            time_utc_str = obs_dt.strftime("%H%M") # '0830'
            
            # Check if this record already exists in our database
            existing = db.query(WeatherData).filter_by(
                year=year, month=month, date=date, time_utc=time_utc_str
            ).first()
            
            if existing:
                continue
                
            # Extract variables safely
            wind_dir = obs.get("wdir")
            # If wind is variable (VRB), it sometimes returns as 'VRB' or 0, converting safely:
            try:
                wind_dir = float(wind_dir)
            except (ValueError, TypeError):
                wind_dir = None
                
            wind_speed = obs.get("wspd")
            
            vis_str = str(obs.get("visib", ""))
            try:
                visibility = float(vis_str.replace('+', '')) if vis_str else None
            except ValueError:
                visibility = None
                
            weather = obs.get("wxString", "")
            
            # Parse clouds
            clouds_data = obs.get("clouds", [])
            clouds_str = " ".join([f"{c.get('cover', '')}{c.get('base', '')}" for c in clouds_data])
            
            temp = obs.get("temp")
            dewp = obs.get("dewp")
            rh = calculate_rh(temp, dewp)
            
            qnh = obs.get("altim")
            
            # Create the database record
            new_record = WeatherData(
                timestamp_utc=obs_dt,
                year=year,
                month=month,
                date=date,
                time_utc=time_utc_str,
                wind_dir=wind_dir,
                wind_speed_kts=wind_speed,
                visibility=visibility,
                weather=weather,
                clouds=clouds_str,
                dry_temp_c=temp,
                dew_point_c=dewp,
                rh_percent=rh,
                qnh_hpa=qnh
            )
            
            db.add(new_record)
            records_added += 1
            
        db.commit()
    except Exception as e:
        print(f"[{datetime.now()}] Database error during live METAR storage: {e}")
        db.rollback()
    finally:
        db.close()
        
    return records_added

if __name__ == "__main__":
    print(f"[{datetime.now()}] Starting manual fetch for the last 24 hours...")
    added = fetch_and_store_live_metar(hours=24)
    print(f"[{datetime.now()}] Manual fetch complete. Added {added} new records.")
