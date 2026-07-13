from fastapi import APIRouter, HTTPException, Depends
import joblib
import pandas as pd
import numpy as np
import os
import sys
from datetime import datetime
from sqlalchemy.orm import Session

from backend.api.schemas import WeatherPredictionRequest, WeatherPredictionResponse
from backend.data.database import get_db
from backend.data.models import WeatherData, PredictionRecord

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
from Models.weather_pipeline import UnifiedWeatherPipeline

router = APIRouter(
    prefix="/weather",
    tags=["Weather Prediction Models"]
)

# Load the AI Models globally
MODEL_DIR = os.path.join(os.path.dirname(__file__), '../../../Models/3h prediction model')
MODEL_PATH = os.path.join(MODEL_DIR, 'weather_model.pkl')
SCALER_PATH = os.path.join(MODEL_DIR, 'scaler.pkl')
FEATURES_PATH = os.path.join(MODEL_DIR, 'feature_columns.pkl')

model = None
scaler = None
feature_columns = None

def load_models():
    global model, scaler, feature_columns
    try:
        if os.path.exists(MODEL_PATH):
            model = joblib.load(MODEL_PATH)
            scaler = joblib.load(SCALER_PATH)
            feature_columns = joblib.load(FEATURES_PATH)
            print("[SUCCESS] 3H Weather prediction model loaded successfully!")
        else:
            print("Warning: Weather models not found. Please run training first.")
    except Exception as e:
        print(f"Error loading models: {e}")

load_models()

def get_historical_dataframe(db: Session, request: WeatherPredictionRequest):
    # Fetch recent historical records from database
    records = db.query(WeatherData).order_by(WeatherData.id.desc()).limit(12).all()
    records.reverse()
    
    data = []
    for r in records:
        data.append({
            'Year': r.year,
            'Month': r.month,
            'Date': r.date,
            'Time(UTC)': str(r.time_utc).zfill(4) if r.time_utc else "0000",
            'Wind Dir.': r.wind_dir,
            'Wind speed(Kts)': r.wind_speed_kts,
            'Dry tem(0C)': r.dry_temp_c,
            'Dew point(0C)': r.dew_point_c,
            'RH(%)': r.rh_percent,
            'QNH (hPa)': r.qnh_hpa,
            'Visibility': r.visibility,
            'Clouds': r.clouds if r.clouds else 'FEW',
            'Weather': r.weather if r.weather else 'NSW'
        })
        
    now = datetime.utcnow()
    time_str = request.time_utc if request.time_utc else now.strftime("%H%M")
    
    # Append the current request as the latest observation point
    data.append({
        'Year': now.year,
        'Month': now.month,
        'Date': now.day,
        'Time(UTC)': time_str,
        'Wind Dir.': request.wind_direction,
        'Wind speed(Kts)': request.wind_speed,
        'Dry tem(0C)': request.temperature,
        'Dew point(0C)': request.dew_point,
        'RH(%)': request.humidity,
        'QNH (hPa)': request.pressure,
        'Visibility': request.visibility,
        'Clouds': 'FEW',
        'Weather': 'NSW'
    })
    
    return pd.DataFrame(data)

@router.post("/predict/3h", response_model=WeatherPredictionResponse)
def predict_weather_3h(request: WeatherPredictionRequest, db: Session = Depends(get_db)):
    global model, scaler, feature_columns
    
    if model is None or scaler is None:
        # Reload models dynamically in case they were retrained
        load_models()
        if model is None or scaler is None:
            raise HTTPException(status_code=500, detail="Weather AI Model is not trained/loaded.")
            
    # Parse UTC time
    time_str = str(request.time_utc).zfill(4) if request.time_utc else datetime.utcnow().strftime("%H%M")
    if len(time_str) != 4 or not time_str.isdigit():
        raise HTTPException(status_code=400, detail="Invalid time_utc format. Use HHMM format (e.g. 0310)")
        
    hour = int(time_str[:2])
    minute = int(time_str[2:])
    
    # Preprocess request input through pipeline using DB history
    df_window = get_historical_dataframe(db, request)
    pipeline = UnifiedWeatherPipeline()
    
    try:
        features_df = pipeline.process_inference_data(df_window, feature_columns)
        
        # Scale and predict
        features_scaled = scaler.transform(features_df)
        prediction = model.predict(features_scaled)[0]
        
        pred_temp = float(prediction[0])
        pred_press = float(prediction[1])
        pred_humidity = float(prediction[2])
        
        # Bound predictions to reasonable values
        pred_humidity = max(0.0, min(100.0, pred_humidity))
        
        # Save record of prediction
        record = PredictionRecord(
            input_temperature=request.temperature,
            input_dew_point=request.dew_point,
            input_humidity=request.humidity,
            input_wind_dir=request.wind_direction,
            input_wind_speed=request.wind_speed,
            input_pressure=request.pressure,
            predicted_temperature=pred_temp,
            predicted_pressure=pred_press,
            predicted_humidity=pred_humidity,
            forecast_type="T+3 Hour Forecast"
        )
        db.add(record)
        db.commit()
        
        forecast_hour = (hour + 3) % 24
        forecast_time_utc = f"{forecast_hour:02d}{minute:02d}"
        
        return WeatherPredictionResponse(
            temperature=round(pred_temp, 2),
            pressure=round(pred_press, 2),
            humidity=round(pred_humidity, 2),
            forecast="T+3 Hour Forecast",
            input_time_utc=time_str,
            forecast_time_utc=forecast_time_utc
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Inference error: {str(e)}")

from backend.mlops_retrainer import run_all_retrainings

@router.post("/models/retrain")
def manual_retrain_models():
    """
    Manually triggers retraining of the operational Random Forest model.
    """
    try:
        results = run_all_retrainings()
        load_models() # reload model
        return {"message": "Retraining complete", "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
