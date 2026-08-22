import os
import sys
import pandas as pd
from datetime import datetime

# Ensure we can import backend modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from backend.data.database import SessionLocal, engine, Base
from backend.data.models import WeatherData
import math

def clean_float(val):
    if pd.isna(val) or type(val) == str:
        return None
    return float(val)

def clean_int(val):
    if pd.isna(val) or type(val) == str:
        return None
    return int(val)

def seed_database():
    """
    Seeds the SQLite database with the last 500 rows of historical data
    so that the Pipeline can calculate rolling averages and lags.
    """
    print("1. Initializing Database...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    print("2. Reading historical Excel file...")
    data_path = os.path.join(os.path.dirname(__file__), '../data/BIA_METAR_DATA_(2019_2024).xlsx')
    df = pd.read_excel(data_path)
    
    print("3. Seeding all records into SQLite...")
    
    # Clear existing data so we don't have duplicates if running again
    db.query(WeatherData).delete()
    db.commit()
    
    # Get all rows instead of just 500
    df_recent = df.copy()
    
    records_to_insert = []
    for _, row in df_recent.iterrows():
        try:
            wd = WeatherData(
                timestamp_utc=datetime.utcnow(),
                year=clean_int(row.get('Year')),
                month=clean_int(row.get('Month')),
                date=clean_int(row.get('Date')),
                time_utc=str(row.get('Time(UTC)')).zfill(4),
                visibility=clean_float(row.get('Visibility')),
                weather=str(row.get('Weather')),
                clouds=str(row.get('Clouds')),
                dry_temp_c=clean_float(row.get('Dry tem(0C)')),
                dew_point_c=clean_float(row.get('Dew point(0C)')),
                rh_percent=clean_float(row.get('RH(%)')),
                qnh_hpa=clean_float(row.get('QNH (hPa)'))
            )
            records_to_insert.append(wd)
        except Exception as e:
            continue
            
    db.add_all(records_to_insert)
    db.commit()
    print(f"[SUCCESS] Successfully seeded {len(records_to_insert)} records into weather_data.db!")
    db.close()

if __name__ == "__main__":
    seed_database()
