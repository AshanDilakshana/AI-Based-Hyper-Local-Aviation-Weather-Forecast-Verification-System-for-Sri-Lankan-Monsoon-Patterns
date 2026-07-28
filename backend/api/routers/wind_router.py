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
MODEL_1H_PATH = os.path.join(os.path.dirname(__file__), '../../../Models/wind_models/1h prediction model/xgboost_wind_model_1h.json')
MODEL_3H_PATH = os.path.join(os.path.dirname(__file__), '../../../Models/wind_models/3h prediction model/xgboost_wind_model_3h.json')

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

def suggest_best_runway(wind_speed: float, wind_dir: float):
    # Calculate for RWY 04 (heading 40)
    crosswind_04, headwind_04 = calculate_aviation_winds(wind_speed, wind_dir, 40)
    # Calculate for RWY 22 (heading 220)
    crosswind_22, headwind_22 = calculate_aviation_winds(wind_speed, wind_dir, 220)
    
    # We prefer the runway with the highest headwind for safe takeoff
    if headwind_22 > headwind_04:
        return 220, abs(crosswind_22), headwind_22, "RWY 22"
    else:
        return 40, abs(crosswind_04), headwind_04, "RWY 04"

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
from backend.data.models import WeatherData, PredictionRecord
import sys
import datetime

# Ensure Models directory is accessible
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
from preprocessing_and_feature_engineering.wind_prediction_model.unified_pipeline import UnifiedWeatherPipeline

def get_historical_dataframe(db_session):
    # Fetch 13 records: 12 for past data + 1 for current live data
    records = db_session.query(WeatherData).order_by(WeatherData.id.desc()).limit(13).all()
    records.reverse()
    
    data = []
    for i, r in enumerate(records):
        is_latest = (i == len(records) - 1)
        data.append({
            'Year': r.year,
            'Month': r.month,
            'Date': r.date,
            'Time(UTC)': str(r.time_utc).zfill(4) if r.time_utc else "0000",
            'Wind Dir': r.wind_dir,
            'Wind speed(Kts)': None if is_latest else r.wind_speed_kts, # Hide target for the row we are predicting
            'Dry Temp(0C)': r.dry_temp_c,
            'Dew point(0C)': r.dew_point_c,
            'RH(%)': r.rh_percent,
            'QNH(hPa)': r.qnh_hpa
        })
        
    return pd.DataFrame(data)

def calculate_target_datetime(df_window, forecast_hours):
    last_row = df_window.iloc[-1]
    time_str = last_row['Time(UTC)']
    year, month, date = last_row['Year'], last_row['Month'], last_row['Date']
    dt = datetime.datetime(year, month, date, int(time_str[:2]), int(time_str[2:]))
    dt_target = dt + datetime.timedelta(hours=forecast_hours)
    return dt_target

@router.post("/predict/1h", response_model=WindPredictionResponse)
def predict_wind_1h(request: WindPredictionRequest):
    if model_1h is None:
        raise HTTPException(status_code=500, detail="1H Wind AI Model is not loaded.")

    db = SessionLocal()
    try:
        df_window = get_historical_dataframe(db)
    finally:
        db.close()

    pipeline = UnifiedWeatherPipeline(forecast_hours=1)
    features = pipeline.process_inference_data(df_window)
    
    # Ensure ordering matches
    expected_cols = pipeline.required_features
    features_ordered = features[expected_cols]
    
    current_wind_dir = float(df_window.iloc[-1]['Wind Dir'])

    predicted_wind_speed = float(model_1h.predict(features_ordered)[0])
    best_heading, crosswind, headwind, runway_name = suggest_best_runway(predicted_wind_speed, current_wind_dir)
    status, message = get_alert_status(crosswind, "1 hour ahead")

    # Save to Database for Verification
    dt_target = calculate_target_datetime(df_window, forecast_hours=1)
    
    db = SessionLocal()
    try:
        new_record = PredictionRecord(
            forecast_type='1H',
            target_year=dt_target.year,
            target_month=dt_target.month,
            target_date=dt_target.day,
            target_time_utc=dt_target.strftime("%H%M"),
            predicted_wind_speed_kts=predicted_wind_speed,
            headwind_kts=headwind,
            crosswind_kts=crosswind,
            status=status
        )
        db.add(new_record)
        db.commit()
    except Exception as e:
        print(f"Failed to save prediction record: {e}")
    finally:
        db.close()

    return WindPredictionResponse(
        predicted_wind_speed_kts=round(predicted_wind_speed, 2),
        headwind_kts=round(headwind, 2),
        crosswind_kts=round(crosswind, 2),
        runway=runway_name,
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
        df_window = get_historical_dataframe(db)
    finally:
        db.close()

    pipeline = UnifiedWeatherPipeline(forecast_hours=3)
    features = pipeline.process_inference_data(df_window)
    
    expected_cols = pipeline.required_features
    features_ordered = features[expected_cols]
    
    current_wind_dir = float(df_window.iloc[-1]['Wind Dir'])

    predicted_wind_speed = float(model_3h.predict(features_ordered)[0])
    best_heading, crosswind, headwind, runway_name = suggest_best_runway(predicted_wind_speed, current_wind_dir)
    status, message = get_alert_status(crosswind, "3 hours ahead")

    # Save to Database for Verification
    dt_target = calculate_target_datetime(df_window, forecast_hours=3)
    
    db = SessionLocal()
    try:
        new_record = PredictionRecord(
            forecast_type='3H',
            target_year=dt_target.year,
            target_month=dt_target.month,
            target_date=dt_target.day,
            target_time_utc=dt_target.strftime("%H%M"),
            predicted_wind_speed_kts=predicted_wind_speed,
            headwind_kts=headwind,
            crosswind_kts=crosswind,
            status=status
        )
        db.add(new_record)
        db.commit()
    except Exception as e:
        print(f"Failed to save prediction record: {e}")
    finally:
        db.close()

    return WindPredictionResponse(
        predicted_wind_speed_kts=round(predicted_wind_speed, 2),
        headwind_kts=round(headwind, 2),
        crosswind_kts=round(crosswind, 2),
        runway=runway_name,
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
