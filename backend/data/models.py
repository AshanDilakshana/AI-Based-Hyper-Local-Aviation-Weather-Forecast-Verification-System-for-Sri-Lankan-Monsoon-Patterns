from sqlalchemy import Column, Integer, Float, String, DateTime
from datetime import datetime
from backend.data.database import Base

class WeatherData(Base):
    __tablename__ = "weather_data"

    id = Column(Integer, primary_key=True, index=True)
    timestamp_utc = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Matching Excel data columns roughly
    year = Column(Integer)
    month = Column(Integer)
    date = Column(Integer)
    time_utc = Column(String)
    
    wind_dir = Column(Float, nullable=True)
    wind_speed_kts = Column(Float, nullable=True)
    visibility = Column(Float, nullable=True)
    weather = Column(String, nullable=True)
    clouds = Column(String, nullable=True)
    
    dry_temp_c = Column(Float, nullable=True)
    dew_point_c = Column(Float, nullable=True)
    rh_percent = Column(Float, nullable=True)
    qnh_hpa = Column(Float, nullable=True)

class PredictionRecord(Base):
    __tablename__ = "prediction_records"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Features used for prediction
    input_temperature = Column(Float)
    input_dew_point = Column(Float)
    input_humidity = Column(Float)
    input_wind_dir = Column(Float)
    input_past_wind_speed = Column(Float)
    
    # Results
    predicted_wind_speed_kts = Column(Float)
    headwind_kts = Column(Float)
    crosswind_kts = Column(Float)
    
    status = Column(String) # SAFE, WARNING, DANGER

class SystemLogs(Base):
    __tablename__ = "system_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp_utc = Column(DateTime, default=datetime.utcnow, index=True)
    level = Column(String, default="INFO") # INFO, ERROR, WARNING, SUCCESS
    component = Column(String) # e.g., MLOps, API
    message = Column(String)
    details = Column(String, nullable=True) # Optional JSON string for extra data like MAE comparison
