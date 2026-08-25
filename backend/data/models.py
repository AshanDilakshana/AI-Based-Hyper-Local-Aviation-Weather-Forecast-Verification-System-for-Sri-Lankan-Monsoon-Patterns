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
    
    visibility = Column(Float, nullable=True)
    weather = Column(String, nullable=True)
    clouds = Column(String, nullable=True)
    
    wind_dir = Column(Float, nullable=True)
    wind_speed_kts = Column(Float, nullable=True)
    
    dry_temp_c = Column(Float, nullable=True)
    dew_point_c = Column(Float, nullable=True)
    rh_percent = Column(Float, nullable=True)
    qnh_hpa = Column(Float, nullable=True)

class PredictionRecord(Base):
    __tablename__ = "prediction_records"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Target Information for Verification
    forecast_type = Column(String) # '1H' or '3H'
    target_year = Column(Integer)
    target_month = Column(Integer)
    target_date = Column(Integer)
    target_time_utc = Column(String)
    
    # Local Times (Not in current SQLite schema)
    # created_at_local = Column(DateTime, nullable=True)
    # target_time_local = Column(String, nullable=True)
    
    # Results (Team's Wind models)
    predicted_wind_speed_kts = Column(Float, nullable=True)
    headwind_kts = Column(Float, nullable=True)
    crosswind_kts = Column(Float, nullable=True)
    
    status = Column(String) # SAFE, WARNING, DANGER
    
    # Errors (Not in current SQLite schema)
    # error_message = Column(String, nullable=True)
    # error_value = Column(Float, nullable=True)

class TempPressurePredictionRecord(Base):
    __tablename__ = "temp_pressure_prediction_records"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Target Information for Verification
    forecast_type = Column(String) # '1H' or '3H'
    target_year = Column(Integer)
    target_month = Column(Integer)
    target_date = Column(Integer)
    target_time_utc = Column(String)
    
    # Results (Imash's models)
    predicted_temperature_c = Column(Float, nullable=True)
    predicted_pressure_hpa = Column(Float, nullable=True)
    
    # Verification & Error Rate Tracking
    actual_temperature_c = Column(Float, nullable=True)
    actual_pressure_hpa = Column(Float, nullable=True)
    temperature_error = Column(Float, nullable=True)
    pressure_error = Column(Float, nullable=True)
    is_verified = Column(Integer, default=0) # 0: Pending, 1: Verified
    
    status = Column(String) # SAFE, WARNING, DANGER




class SystemLogs(Base):
    __tablename__ = "system_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp_utc = Column(DateTime, default=datetime.utcnow, index=True)
    level = Column(String, default="INFO") # INFO, ERROR, WARNING, SUCCESS
    component = Column(String) # e.g., MLOps, API
    message = Column(String)
    details = Column(String, nullable=True) # Optional JSON string for extra data like MAE comparison


class VerifiedForecast(Base):
    __tablename__ = "verified_forecasts"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow) # Time forecast was saved
    target_time = Column(DateTime) # Target valid time
    
    # Weather metrics
    dry_temp_c = Column(Float, nullable=True)
    wind_speed_kts = Column(Float, nullable=True)
    wind_dir = Column(Float, nullable=True)
    rh_percent = Column(Float, nullable=True)
    clouds = Column(String, nullable=True)
    visibility = Column(Float, nullable=True)
    qnh_hpa = Column(Float, nullable=True)
    headwind_kts = Column(Float, nullable=True)
    crosswind_kts = Column(Float, nullable=True)
