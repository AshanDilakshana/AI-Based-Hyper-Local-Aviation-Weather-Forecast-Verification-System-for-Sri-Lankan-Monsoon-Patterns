from fastapi import APIRouter, HTTPException
import xgboost as xgb
import pandas as pd
import numpy as np
import os
from backend.api.schemas import WindPredictionRequest, WindPredictionResponse

router = APIRouter(
    prefix="/wind",
    tags=["Wind Prediction Models"]
)

# Load the AI Models globally for this router
# Corrected paths pointing to the 'Models' folder
MODEL_1H_PATH = os.path.join(os.path.dirname(__file__), '../../../Models/1h prediction model/xgboost_wind_model.json')
MODEL_3H_PATH = os.path.join(os.path.dirname(__file__), '../../../Models/3h prediction model/xgboost_wind_model_3h.json')

model_1h = None
model_3h = None

def load_models():
    global model_1h, model_3h
    
    try:
        model_1h = xgb.XGBRegressor()
        model_1h.load_model(MODEL_1H_PATH)
    except Exception as e:
        print(f"Warning: Could not load 1H wind model. Trying backup. Error: {e}")
        try:
            backup_path = MODEL_1H_PATH.replace('.json', '_backup.json')
            model_1h = xgb.XGBRegressor()
            model_1h.load_model(backup_path)
            print("Loaded 1H BACKUP model.")
        except Exception:
            print("CRITICAL: Failed to load 1H model and backup.")
            model_1h = None

    try:
        model_3h = xgb.XGBRegressor()
        model_3h.load_model(MODEL_3H_PATH)
    except Exception as e:
        print(f"Warning: Could not load 3H wind model. Trying backup. Error: {e}")
        try:
            backup_path = MODEL_3H_PATH.replace('.json', '_backup.json')
            model_3h = xgb.XGBRegressor()
            model_3h.load_model(backup_path)
            print("Loaded 3H BACKUP model.")
        except Exception:
            print("CRITICAL: Failed to load 3H model and backup.")
            model_3h = None

load_models()

def calculate_aviation_winds(wind_speed: float, wind_dir: float, runway_heading: int):
    """Calculates Headwind and Crosswind for a specific runway."""
    angle_diff = np.radians(wind_dir - runway_heading)
    crosswind = wind_speed * np.sin(angle_diff)
    headwind = wind_speed * np.cos(angle_diff)
    return abs(crosswind), headwind

def get_alert_status(crosswind: float, timeframe_str: str):
    status = "SAFE"
    message = f"Forecast for {timeframe_str}: Crosswind components are within normal limits."
    if crosswind > 15:
        status = "WARNING"
        message = f"Forecast for {timeframe_str}: High crosswind likely! Plan contingencies."
    if crosswind > 25:
        status = "DANGER"
        message = f"Forecast for {timeframe_str}: Severe crosswind. Exceeds standard operating limits."
    return status, message

from backend.data.database import SessionLocal
from backend.data.models import WeatherData
import sys
import datetime

# Ensure Models directory is accessible
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
from Models.wind_pipeline import UnifiedWeatherPipeline

def get_historical_dataframe(db_session, current_request):
    records = db_session.query(WeatherData).order_by(WeatherData.id.desc()).limit(12).all()
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
            'QNH(hPa)': r.qnh_hpa
        })
        
    now = datetime.datetime.utcnow()
    data.append({
        'Year': now.year,
        'Month': now.month,
        'Date': now.day,
        'Time(UTC)': str(current_request.time_utc).zfill(4) if current_request.time_utc else now.strftime("%H%M"),
        'Wind Dir': current_request.wind_dir,
        'Wind speed(Kts)': None, 
        'Dry Temp(0C)': current_request.temperature,
        'Dew point(0C)': current_request.dew_point,
        'RH(%)': current_request.humidity,
        'QNH(hPa)': current_request.qnh_hpa
    })
    
    return pd.DataFrame(data)

@router.post("/predict/1h", response_model=WindPredictionResponse)
def predict_wind_1h(request: WindPredictionRequest):
    if model_1h is None:
        raise HTTPException(status_code=500, detail="1H Wind AI Model is not loaded.")

    db = SessionLocal()
    try:
        df_window = get_historical_dataframe(db, request)
    finally:
        db.close()

    pipeline = UnifiedWeatherPipeline(forecast_hours=1)
    features = pipeline.process_inference_data(df_window)
    
    # Ensure ordering matches
    expected_cols = pipeline.required_features
    features_ordered = features[expected_cols]

    predicted_wind_speed = float(model_1h.predict(features_ordered)[0])
    crosswind, headwind = calculate_aviation_winds(predicted_wind_speed, request.wind_dir, request.runway_heading)
    status, message = get_alert_status(crosswind, "1 hour ahead")

    return WindPredictionResponse(
        predicted_wind_speed_kts=round(predicted_wind_speed, 2),
        headwind_kts=round(headwind, 2),
        crosswind_kts=round(crosswind, 2),
        runway=f"RWY {str(request.runway_heading).zfill(3)}",
        status=status,
        message=message
    )

@router.post("/predict/3h", response_model=WindPredictionResponse)
def predict_wind_3h(request: WindPredictionRequest):
    if model_3h is None:
        raise HTTPException(status_code=500, detail="3H Wind AI Model is not loaded.")

    if request.time_utc is None or request.qnh_hpa is None:
        raise HTTPException(status_code=400, detail="time_utc and qnh_hpa are required for the 3H model.")

    db = SessionLocal()
    try:
        df_window = get_historical_dataframe(db, request)
    finally:
        db.close()

    pipeline = UnifiedWeatherPipeline(forecast_hours=3)
    features = pipeline.process_inference_data(df_window)
    
    expected_cols = pipeline.required_features
    features_ordered = features[expected_cols]

    predicted_wind_speed = float(model_3h.predict(features_ordered)[0])
    crosswind, headwind = calculate_aviation_winds(predicted_wind_speed, request.wind_dir, request.runway_heading)
    status, message = get_alert_status(crosswind, "3 hours ahead")

    return WindPredictionResponse(
        predicted_wind_speed_kts=round(predicted_wind_speed, 2),
        headwind_kts=round(headwind, 2),
        crosswind_kts=round(crosswind, 2),
        runway=f"RWY {str(request.runway_heading).zfill(3)}",
        status=status,
        message=message
    )

from backend.mlops_retrainer import run_all_retrainings

@router.post("/models/retrain")
def manual_retrain_models():
    """
    Manually triggers the MLOps retraining pipeline.
    """
    try:
        results = run_all_retrainings()
        load_models() # Hot-reload models into memory
        return {"message": "Retraining complete", "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
