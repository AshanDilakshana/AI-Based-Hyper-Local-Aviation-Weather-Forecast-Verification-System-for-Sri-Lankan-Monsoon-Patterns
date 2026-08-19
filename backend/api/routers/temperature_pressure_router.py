from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import joblib
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List
from backend.data.database import SessionLocal
from backend.data.models import PredictionRecord
from preprocessing_and_feature_engineering.temperature_pressure_model.unified_pipeline import UnifiedWeatherPipeline
from backend.data.models import WeatherData
import sqlite3

router = APIRouter(prefix="/predict", tags=["Temperature & Pressure Forecast"])

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DB_PATH = os.path.join(BASE_DIR, "weather_data.db") 
MODEL_DIR = os.path.join(BASE_DIR, "Models", "Temperature")

# Global variables to hold models
temp_model = None
temp_scaler = None
temp_features = []
pressure_model = None
pressure_scaler = None
pressure_features = []

def load_Temp_Press_models():
    """Loads Temperature and Pressure models into memory."""
    global temp_model, temp_scaler, temp_features
    global pressure_model, pressure_scaler, pressure_features
    try:
        temp_model = joblib.load(os.path.join(MODEL_DIR, "temp_model.pkl"))
        temp_scaler = joblib.load(os.path.join(MODEL_DIR, "temp_scaler.pkl"))
        temp_features = joblib.load(os.path.join(MODEL_DIR, "temp_feature_columns.pkl"))

        pressure_model = joblib.load(os.path.join(MODEL_DIR, "pressure_model.pkl"))
        pressure_scaler = joblib.load(os.path.join(MODEL_DIR, "pressure_scaler.pkl"))
        pressure_features = joblib.load(os.path.join(MODEL_DIR, "pressure_feature_columns.pkl"))
        print("Temperature and Pressure models loaded successfully.")
    except Exception as e:
        print(f"Warning: Separate models not fully trained or found yet. Error: {e}")

# Call immediately to load models on startup
load_Temp_Press_models()

class ObservationRequest(BaseModel):
    obs_time: int
    temperature: float
    humidity: float
    pressure: float
    dew_point: float
    wind_speed: float
    wind_direction: float
    visibility: float
    report_time: str
    
    class Config:
        extra = "allow" # allow extra fields

def get_historical_dataframe(db_session, limit=48):
    # Fetch records to cover lag48 and roll24
    records = db_session.query(WeatherData).order_by(WeatherData.id.desc()).limit(limit).all()
    records.reverse()
    
    data = []
    for r in records:
        data.append({
            'Year': r.year,
            'Month': r.month,
            'Date': r.date,
            'Time(UTC)': str(r.time_utc).zfill(4) if r.time_utc else "0000",
            'Wind Dir': r.wind_dir,
            'Wind speed(Kts)': r.wind_speed_kts,
            'Dry Temp(0C)': r.dry_temp_c,
            'Dew point(0C)': r.dew_point_c,
            'RH(%)': r.rh_percent,
            'QNH(hPa)': r.qnh_hpa,
            'visibility': r.visibility
        })
        
    return pd.DataFrame(data)

@router.post("/temp-press")
def predict_temperature_and_pressure(obs: ObservationRequest):
    """
    Predicts Temperature and Pressure 3 hours ahead using local random forest models.
    """
    if not temp_model or not pressure_model:
        raise HTTPException(status_code=503, detail="Models are not loaded.")

    db = SessionLocal()
    try:
        # Fetch enough historical data for lags up to 48
        df_window = get_historical_dataframe(db, limit=50)
    finally:
        db.close()
        
    # Append the current observation if we need it, though normally API has it in DB.
    # We will assume we just use the historical window for inference.
    if len(df_window) == 0:
        raise HTTPException(status_code=400, detail="Not enough historical data in DB for time-series features.")
        
    pipeline = UnifiedWeatherPipeline()
    temp_feats, press_feats = pipeline.process_inference_data(df_window)
    
    try:
        # Scaling and Prediction
        df_temp_scaled = temp_scaler.transform(temp_feats)
        pred_temp = temp_model.predict(df_temp_scaled)[0]

        df_press_scaled = pressure_scaler.transform(press_feats)
        pred_press = pressure_model.predict(df_press_scaled)[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {e}")

    obs_data = obs.dict()
    dt = datetime.strptime(obs_data["report_time"][:19], "%Y-%m-%dT%H:%M:%S")
    dt_out = dt + timedelta(hours=3)
    
    # --- Save Prediction to Database ---
    try:
        db = SessionLocal()
        new_pred = PredictionRecord(
            forecast_type='3H',
            target_year=dt_out.year,
            target_month=dt_out.month,
            target_date=dt_out.day,
            target_time_utc=dt_out.strftime("%H%M"),
            predicted_temperature_c=float(pred_temp),
            predicted_pressure_hpa=float(pred_press),
            status="SAFE"
        )
        db.add(new_pred)
        db.commit()
        db.close()
    except Exception as db_err:
        print(f"Warning: Could not save prediction to DB: {db_err}")
    # -----------------------------------

    return {
        "input_obs_time": obs_data["obs_time"],
        "forecast_time": obs_data["obs_time"] + 10800,
        "predicted_temperature": round(float(pred_temp), 2),
        "predicted_pressure": round(float(pred_press), 2),
        "forecast_report_time": dt_out.strftime("%Y-%m-%dT%H:%M:%S"),
        "input_report_time": obs_data["report_time"]
    }
