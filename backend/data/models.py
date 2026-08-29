from sqlalchemy import Column, Integer, Float, String, DateTime, Boolean
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

class SystemLogs(Base):
    __tablename__ = "system_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp_utc = Column(DateTime, default=datetime.utcnow, index=True)
    level = Column(String, default="INFO") # INFO, ERROR, WARNING, SUCCESS
    component = Column(String) # e.g., MLOps, API
    message = Column(String)
    details = Column(String, nullable=True) # Optional JSON string for extra data like MAE comparison

class ModelsForecast(Base):
    __tablename__ = "Mdels_focast"
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    target_time_utc = Column(DateTime, index=True)
    
    wind_speed_kts = Column(Float, nullable=True)
    wind_dir = Column(Float, nullable=True)
    temperature_c = Column(Float, nullable=True)
    pressure_hpa = Column(Float, nullable=True)
    visibility = Column(Float, nullable=True)
    clouds = Column(String, nullable=True)
    dew_point_c = Column(Float, nullable=True)
    rh_percent = Column(Float, nullable=True)
    qnh_hpa = Column(Float, nullable=True)

class VerifiedForecast(Base):
    __tablename__ = "Verified_Forcast"
    
    id = Column(Integer, primary_key=True, index=True)
    target_time = Column(DateTime, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    dry_temp_c = Column(Float, nullable=True)
    wind_speed_kts = Column(Float, nullable=True)
    wind_dir = Column(Float, nullable=True)
    rh_percent = Column(Float, nullable=True)
    clouds = Column(String, nullable=True)
    visibility = Column(Float, nullable=True)
    qnh_hpa = Column(Float, nullable=True)
    headwind_kts = Column(Float, nullable=True)
    crosswind_kts = Column(Float, nullable=True)
    remarks = Column(String, nullable=True)

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True) # Also used as reference/Licence Number
    hashed_password = Column(String)
    role = Column(String) # 'forecaster' or 'pilot'
    name = Column(String)
    email = Column(String, nullable=True)
    organisation = Column(String, nullable=True)
    station = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)

class RouteAlternatives(Base):
    __tablename__ = "route_alternatives"
    
    id = Column(Integer, primary_key=True, index=True)
    region_name = Column(String, unique=True, index=True)
    airports = Column(String) # Comma-separated list of ICAO codes

class FlightTimeAndFlights(Base):
    __tablename__ = "flight_time_and_flights"
    
    id = Column(Integer, primary_key=True, index=True)
    flight = Column(String, nullable=True) # e.g. UL604
    departure_time_local = Column(String, nullable=True) # e.g. 00:25
    destination = Column(String, index=True) # e.g. MEL
    time_period_mins = Column(Integer, nullable=True) # e.g. 580

class PilotFlightPlan(Base):
    __tablename__ = "pilot_flight_plan"
    
    id = Column(Integer, primary_key=True, index=True)
    pilot_reference = Column(String, index=True) # Pilot username/reference ID
    flight_no = Column(String)
    departure = Column(String)
    destination = Column(String)
    departure_time = Column(DateTime)
    duration_mins = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
