import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '')))
from backend.data.database import SessionLocal
from backend.data.models import ModelsForecast
from datetime import datetime

db = SessionLocal()
now = datetime.utcnow()
forecasts = db.query(ModelsForecast).filter(ModelsForecast.target_time_utc >= now).order_by(ModelsForecast.target_time_utc.asc()).limit(10).all()
for f in forecasts:
    print(f.target_time_utc, f.temperature_c, f.wind_speed_kts)
