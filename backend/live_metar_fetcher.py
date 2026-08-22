import os
import sys
import requests
import sqlite3
import re
from datetime import datetime

# DB Path configuration
base_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(base_dir, '../'))
db_path = os.path.abspath(os.path.join(project_root, 'weather_data.db'))

API_URL = "https://aviationweather.gov/api/data/metar?ids=VCBI&format=json"

def calculate_rh(temp, dewp):
    if temp is None or dewp is None:
        return None
    # Magnus-Tetens approximation
    e = 6.11 * (10 ** (7.5 * temp / (237.3 + temp)))
    es = 6.11 * (10 ** (7.5 * dewp / (237.3 + dewp)))
    return round((es / e) * 100, 2)

def extract_visibility_from_raw(raw_ob):
    match = re.search(r'KT\s+(\d{4})', raw_ob)
    if match:
        return float(match.group(1))
    return 9999.0 # fallback

def extract_weather_and_clouds(raw_ob):
    parts = raw_ob.split(' ')
    clouds = []
    weather = []
    
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
        " ".join(weather) if weather else "NONE"
    )

def fetch_and_store_live_metar(hours=2):
    print(f"[{datetime.utcnow()}] Fetching live METAR data for VCBI (Last {hours} hours)...")
    
    url = f"https://aviationweather.gov/api/data/metar?ids=VCBI&format=json&hours={hours}"
    
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if not data or len(data) == 0:
            print("[WARNING] No data returned from API.")
            return
            
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        records_added = 0
        for ob in reversed(data):
            raw_ob = ob.get('rawOb', '')
            report_time_str = ob.get('reportTime')
            if not report_time_str: continue
                
            dt = datetime.strptime(report_time_str, "%Y-%m-%dT%H:%M:%S.000Z")
            
            year, month, date, time_utc = dt.year, dt.month, dt.day, dt.strftime("%H%M")
            
            # Check if exists
            cursor.execute("SELECT 1 FROM weather_data WHERE year=? AND month=? AND date=? AND time_utc=?", (year, month, date, time_utc))
            if cursor.fetchone():
                continue
                
            wind_dir = float(ob.get('wdir')) if ob.get('wdir') is not None else None
            wind_speed_kts = float(ob.get('wspd')) if ob.get('wspd') is not None else None
            dry_temp_c = float(ob.get('temp')) if ob.get('temp') is not None else None
            dew_point_c = float(ob.get('dewp')) if ob.get('dewp') is not None else None
            qnh_hpa = float(ob.get('altim')) if ob.get('altim') is not None else None
            
            rh_percent = calculate_rh(dry_temp_c, dew_point_c)
            visibility = extract_visibility_from_raw(raw_ob)
            clouds, weather = extract_weather_and_clouds(raw_ob)
            
            cursor.execute("""
                INSERT INTO weather_data 
                (timestamp_utc, year, month, date, time_utc, wind_dir, wind_speed_kts, visibility, weather, clouds, dry_temp_c, dew_point_c, rh_percent, qnh_hpa) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), year, month, date, time_utc, wind_dir, wind_speed_kts, visibility, weather, clouds, dry_temp_c, dew_point_c, rh_percent, qnh_hpa))
            records_added += 1
            
        conn.commit()
        conn.close()
        
        if records_added > 0:
            print(f"[SUCCESS] Added {records_added} new live METAR record(s).")
        else:
            print("[INFO] No new METAR records. All fetched data already exists in DB.")
            
    except Exception as e:
        print(f"[ERROR] Error fetching live METAR: {e}")

if __name__ == "__main__":
    fetch_and_store_live_metar(hours=2)
