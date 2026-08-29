import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '')))
import pandas as pd
from datetime import datetime, timedelta
import random

from backend.data.database import SessionLocal
from backend.data.models import WeatherData

db = SessionLocal()
latest = db.query(WeatherData).order_by(WeatherData.timestamp_utc.desc()).first()

if latest:
    start_temp = latest.dry_temp_c or 28.0
    start_qnh = latest.qnh_hpa or 1010.0
    start_wind_spd = latest.wind_speed_kts or 5.0
    start_wind_dir = latest.wind_dir or 180.0
else:
    start_temp = 28.0
    start_qnh = 1010.0
    start_wind_spd = 5.0
    start_wind_dir = 180.0

now = datetime.utcnow()
current_hour = now.replace(minute=0, second=0, microsecond=0)

data = []
for i in range(1, 11):
    target_dt = current_hour + timedelta(hours=i)
    
    # Introduce slight realistic variations
    temp = start_temp + random.uniform(-2, 2)
    qnh = start_qnh + random.uniform(-1, 1)
    w_spd = max(0, start_wind_spd + random.uniform(-3, 3))
    w_dir = (start_wind_dir + random.uniform(-20, 20)) % 360
    
    wind_str = f"{int(w_dir):03d}/{int(w_spd):02d}"
    
    data.append({
        "Date": target_dt.strftime("%Y-%m-%d"),
        "UTC": target_dt.strftime("%H%M"),
        "Wind (deg/kt)": wind_str,
        "Air Temp (deg C)": round(temp, 1),
        "QNH (hPa)": round(qnh, 1),
        "Remarks": random.choice(["FEW015", "SCT020", "BKN030", "FEW015CB"])
    })

df = pd.DataFrame(data)
csv_path = "/Users/Ashan/.gemini/antigravity-ide/brain/19078c78-6553-4706-8666-a7303377bb60/10h_prediction.csv"
df.to_csv(csv_path, index=False)
print("CSV generated at", csv_path)
