from fastapi import APIRouter, HTTPException
import pandas as pd
import os
import random
import math

router = APIRouter(
    prefix="/mock-metrology",
    tags=["Mock Metrology Data API"]
)

# Load data into memory once
DATA_PATH = os.path.join(os.path.dirname(__file__), '../../../BIA_METAR_DATA_(2019_2024).xlsx')
df = None

try:
    df = pd.read_excel(DATA_PATH)
except Exception as e:
    print(f"Warning: Could not load mock Excel data: {e}")

def clean_float(val):
    if pd.isna(val):
        return None
    try:
        f_val = float(val)
        if math.isnan(f_val):
            return None
        return f_val
    except (ValueError, TypeError):
        return None

def clean_int(val):
    if pd.isna(val):
        return None
    try:
        f_val = float(val)
        if math.isnan(f_val):
            return None
        return int(f_val)
    except (ValueError, TypeError):
        return None

@router.get("/current")
def get_current_mock_weather():
    """
    Simulates a live data API by returning a random row from the historical dataset.
    """
    global df
    if df is None:
        raise HTTPException(status_code=500, detail="Mock data source not available.")
    
    # Pick a random row
    random_index = random.randint(0, len(df) - 1)
    row = df.iloc[random_index]
    
    return {
        "timestamp_simulated": "now",
        "year": clean_int(row.get('Year')),
        "month": clean_int(row.get('Month')),
        "date": clean_int(row.get('Date')),
        "time_utc": str(row.get('Time(UTC)')),
        "metar_speci": str(row.get('METAR /SPECI')),
        "wind_dir": clean_float(row.get('Wind Dir.')),
        "wind_speed_kts": clean_float(row.get('Wind speed(Kts)')),
        "visibility": clean_float(row.get('Visibility')),
        "weather": str(row.get('Weather')),
        "clouds": str(row.get('Clouds')),
        "dry_temp_c": clean_float(row.get('Dry tem(0C)')),
        "dew_point_c": clean_float(row.get('Dew point(0C)')),
        "rh_percent": clean_float(row.get('RH(%)')),
        "qnh_hpa": clean_float(row.get('QNH (hPa)'))
    }
