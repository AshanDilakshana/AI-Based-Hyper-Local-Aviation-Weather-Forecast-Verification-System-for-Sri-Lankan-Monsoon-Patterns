from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import pandas as pd
import joblib
import os
import numpy as np
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from backend.api.physics_utils import (
    calculate_pressure_altitude, 
    calculate_isa_temperature, 
    calculate_density_altitude, 
    classify_vcbi_density_altitude, 
    get_aviation_performance_impact
)
from tensorflow.keras.models import load_model

# Adjust paths assuming this file is in backend/api/routers/
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
MODEL_DIR = os.path.join(BASE_DIR, "Models", "Temperature", "random_forest")

import sys
sys.path.append(BASE_DIR)

from backend.data.database import get_db
from backend.data.models import TempPressurePredictionRecord, WeatherData

router = APIRouter(prefix="/predict", tags=["Temperature & Pressure Forecast"])

from backend.api.schemas import TempPressPredictionRequest

# Global model instance
temp_model = None
temp_scaler = None
temp_features = None

press_model = None
press_scaler = None
press_features = None

lstm_model = None
hybrid_model = None
lstm_scaler_X = None
lstm_scaler_y = None

def load_Temp_Press_models():
    """Loads the Temperature & Pressure models into memory."""
    global temp_model, temp_scaler, temp_features, press_model, press_scaler, press_features
    global lstm_model, hybrid_model, lstm_scaler_X, lstm_scaler_y
    try:
        temp_model = joblib.load(os.path.join(MODEL_DIR, "temp_model.pkl"))
        temp_scaler = joblib.load(os.path.join(MODEL_DIR, "temp_scaler.pkl"))
        temp_features = joblib.load(os.path.join(MODEL_DIR, "temp_feature_columns.pkl"))
        
        press_model = joblib.load(os.path.join(MODEL_DIR, "pressure_model.pkl"))
        press_scaler = joblib.load(os.path.join(MODEL_DIR, "pressure_scaler.pkl"))
        press_features = joblib.load(os.path.join(MODEL_DIR, "pressure_feature_columns.pkl"))
        
        lstm_model = load_model(os.path.join(MODEL_DIR, "..", "lstm_hybrid", "lstm_model.keras"), compile=False)
        hybrid_model = joblib.load(os.path.join(MODEL_DIR, "..", "lstm_hybrid", "hybrid_rf_model.pkl"))
        lstm_scaler_X = joblib.load(os.path.join(MODEL_DIR, "..", "lstm_hybrid", "lstm_scaler_X.pkl"))
        lstm_scaler_y = joblib.load(os.path.join(MODEL_DIR, "..", "lstm_hybrid", "lstm_scaler_y.pkl"))
        
        print("Temperature & Pressure models loaded successfully.")
    except Exception as e:
        print(f"Warning: Temperature & Pressure models could not be loaded: {e}")

# Call immediately on module load
load_Temp_Press_models()


def prepare_features_with_lags(db: Session, current_data: dict = None):
    # Fetch last 4 records (to get current + 3 lags, or if current_data is provided, just 3 lags)
    recent_records = db.query(WeatherData).order_by(WeatherData.timestamp_utc.desc()).limit(4).all()
    
    if len(recent_records) == 0:
        raise ValueError("Not enough historical data in DB to generate lag features.")
        
    # Pad records if less than 4
    while len(recent_records) < 4:
        recent_records.append(recent_records[-1])
        
    recent_records.reverse() # chronologically: oldest to newest
    
    # We will build a dataframe to create lag features identically to training
    data = []
    for r in recent_records:
        data.append({
            'year': r.year,
            'month': r.month,
            'date': r.date,
            'time_utc': r.time_utc,
            'wind_dir': r.wind_dir,
            'wind_speed_kts': r.wind_speed_kts,
            'visibility': r.visibility,
            'dry_temp_c': r.dry_temp_c,
            'dew_point_c': r.dew_point_c,
            'rh_percent': r.rh_percent,
            'qnh_hpa': r.qnh_hpa
        })
        
    df = pd.DataFrame(data)
    
    if current_data is not None:
        # Override the most recent row with the manual current_data provided by user
        idx = df.index[-1]
        df.at[idx, 'dry_temp_c'] = current_data.get('temperature', df.at[idx, 'dry_temp_c'])
        df.at[idx, 'qnh_hpa'] = current_data.get('pressure', df.at[idx, 'qnh_hpa'])
        df.at[idx, 'rh_percent'] = current_data.get('humidity', df.at[idx, 'rh_percent'])
        df.at[idx, 'dew_point_c'] = current_data.get('dew_point', df.at[idx, 'dew_point_c'])
        df.at[idx, 'wind_speed_kts'] = current_data.get('wind_speed', df.at[idx, 'wind_speed_kts'])
        df.at[idx, 'wind_dir'] = current_data.get('wind_direction', df.at[idx, 'wind_dir'])
        df.at[idx, 'visibility'] = current_data.get('visibility', df.at[idx, 'visibility'])
    
    for i in range(1, 4):
        df[f'qnh_hpa_lag_{i}'] = df['qnh_hpa'].shift(i)
        df[f'dry_temp_c_lag_{i}'] = df['dry_temp_c'].shift(i)
        df[f'rh_percent_lag_{i}'] = df['rh_percent'].shift(i)
        
    # Get the last row which now has all lag features populated
    latest_row = df.iloc[[-1]].copy()
    
    latest_row = latest_row.select_dtypes(include=[np.number])
    latest_row = latest_row.replace([np.inf, -np.inf], np.nan)
    latest_row = latest_row.fillna(0) # simplistic imputation for inference
    
    return latest_row

def prepare_lstm_sequence(db: Session, current_data: dict = None):
    SEQ_LEN = 12
    recent_records = db.query(WeatherData).order_by(WeatherData.timestamp_utc.desc()).limit(SEQ_LEN).all()
    if len(recent_records) < SEQ_LEN:
        while len(recent_records) < SEQ_LEN:
            recent_records.append(recent_records[-1] if len(recent_records)>0 else WeatherData(dry_temp_c=30, qnh_hpa=1010))
    recent_records.reverse()
    
    data = []
    for r in recent_records:
        data.append([r.dry_temp_c or 30.0, r.qnh_hpa or 1010.0])
        
    if current_data is not None:
        data[-1][0] = current_data.get('temperature', data[-1][0])
        data[-1][1] = current_data.get('pressure', data[-1][1])
        
    return np.array(data)

@router.post("/run-active-prediction")
def run_active_prediction(db: Session = Depends(get_db)):
    """Runs a prediction based entirely on the latest data in the database."""
    if temp_model is None or press_model is None:
        raise HTTPException(status_code=500, detail="Temperature/Pressure models are not loaded.")
        
    try:
        df = prepare_features_with_lags(db)
        
        # Make sure columns match what the model expects
        X_temp = df.reindex(columns=temp_features, fill_value=0)
        X_temp_scaled = temp_scaler.transform(X_temp)
        predicted_temp = float(temp_model.predict(X_temp_scaled)[0])
        
        X_press = df.reindex(columns=press_features, fill_value=0)
        X_press_scaled = press_scaler.transform(X_press)
        predicted_press_diff = float(press_model.predict(X_press_scaled)[0])
        
        current_pressure = float(df['qnh_hpa'].iloc[0])
        predicted_press = current_pressure + predicted_press_diff
        
        try:
            seq = prepare_lstm_sequence(db)
            seq_scaled = lstm_scaler_X.transform(seq)
            seq_scaled = np.expand_dims(seq_scaled, axis=0)
            
            lstm_pred_scaled = lstm_model.predict(seq_scaled, verbose=0)
            lstm_pred = lstm_scaler_y.inverse_transform(lstm_pred_scaled)[0]
            
            curr_temp = seq[-1][0]
            curr_press = seq[-1][1]
            hybrid_features = np.array([[curr_temp, curr_press, lstm_pred[0], lstm_pred[1]]])
            
            final_pred = hybrid_model.predict(hybrid_features)[0]
            predicted_temp = float(final_pred[0])
            predicted_press = float(final_pred[1])
        except Exception as e:
            print("Hybrid failed, falling back to RF:", e)
            
        pa = calculate_pressure_altitude(predicted_press)
        isa = calculate_isa_temperature(pa)
        da = calculate_density_altitude(pa, predicted_temp, isa)
        classification = classify_vcbi_density_altitude(da)
        impact = get_aviation_performance_impact(classification)
        
        # The latest record we just predicted from
        latest_record = db.query(WeatherData).order_by(WeatherData.timestamp_utc.desc()).first()
        
        target_time = datetime.utcnow() + timedelta(hours=3)
        
        record = TempPressurePredictionRecord(
            created_at=datetime.utcnow(),
            forecast_type="3H",
            target_year=target_time.year,
            target_month=target_time.month,
            target_date=target_time.day,
            target_time_utc=target_time.strftime("%H%M"),
            predicted_temperature_c=predicted_temp,
            predicted_pressure_hpa=predicted_press,
            status="SAFE"
        )
        
        db.add(record)
        
        from backend.data.models import ModelsForecast
        unified_record = ModelsForecast(
            target_time_utc=target_time,
            model_type='Temp_Press_3H',
            temperature_c=predicted_temp,
            pressure_hpa=predicted_press
        )
        db.add(unified_record)
        
        db.commit()
        db.refresh(record)
        
        return {
            "id": record.id,
            "forecast_report_time": target_time.isoformat(),
            "predicted_temperature": round(predicted_temp, 2),
            "predicted_pressure": round(predicted_press, 2),
            "input_report_time": latest_record.timestamp_utc.isoformat() if latest_record.timestamp_utc else datetime.utcnow().isoformat(),
            "derived_parameters": {
                "pressure_altitude_ft": round(pa, 2),
                "isa_temperature_c": round(isa, 2),
                "density_altitude_ft": round(da, 2),
                "classification": classification,
                "performance_impact": impact
            }
        }
        
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/temp-press")
def predict_temperature_pressure(request: TempPressPredictionRequest, db: Session = Depends(get_db)):
    if temp_model is None or press_model is None:
        raise HTTPException(status_code=500, detail="Temperature/Pressure models are not loaded.")
        
    try:
        # Use manual input for current data, fetch lags from DB
        df = prepare_features_with_lags(db, request.dict())
        
        X_temp = df.reindex(columns=temp_features, fill_value=0)
        X_temp_scaled = temp_scaler.transform(X_temp)
        predicted_temp = float(temp_model.predict(X_temp_scaled)[0])
        
        X_press = df.reindex(columns=press_features, fill_value=0)
        X_press_scaled = press_scaler.transform(X_press)
        predicted_press_diff = float(press_model.predict(X_press_scaled)[0])
        
        current_pressure = request.pressure
        predicted_press = current_pressure + predicted_press_diff
        
        try:
            seq = prepare_lstm_sequence(db, request.dict())
            seq_scaled = lstm_scaler_X.transform(seq)
            seq_scaled = np.expand_dims(seq_scaled, axis=0)
            
            lstm_pred_scaled = lstm_model.predict(seq_scaled, verbose=0)
            lstm_pred = lstm_scaler_y.inverse_transform(lstm_pred_scaled)[0]
            
            curr_temp = seq[-1][0]
            curr_press = seq[-1][1]
            hybrid_features = np.array([[curr_temp, curr_press, lstm_pred[0], lstm_pred[1]]])
            
            final_pred = hybrid_model.predict(hybrid_features)[0]
            predicted_temp = float(final_pred[0])
            predicted_press = float(final_pred[1])
        except Exception as e:
            print("Hybrid failed, falling back to RF:", e)
            
        pa = calculate_pressure_altitude(predicted_press)
        isa = calculate_isa_temperature(pa)
        da = calculate_density_altitude(pa, predicted_temp, isa)
        classification = classify_vcbi_density_altitude(da)
        impact = get_aviation_performance_impact(classification)
        
        target_time = datetime.utcnow() + timedelta(hours=3)
        created_at_utc = datetime.utcnow()
        sl_tz_offset = timedelta(hours=5, minutes=30)
        
        record = TempPressurePredictionRecord(
            created_at=created_at_utc,
            forecast_type="3H_MANUAL",
            target_year=target_time.year,
            target_month=target_time.month,
            target_date=target_time.day,
            target_time_utc=target_time.strftime("%H%M"),
            predicted_temperature_c=predicted_temp,
            predicted_pressure_hpa=predicted_press,
            status="SAFE"
        )
        db.add(record)
        
        from backend.data.models import ModelsForecast
        unified_record = ModelsForecast(
            target_time_utc=target_time,
            model_type='Temp_Press_3H_Manual',
            temperature_c=predicted_temp,
            pressure_hpa=predicted_press
        )
        db.add(unified_record)
        
        db.commit()
        
        return {
            "prediction": {
                "temperature_C": round(predicted_temp, 2),
                "pressure_hPa": round(predicted_press, 2)
            },
            "derived_parameters": {
                "pressure_altitude_ft": round(pa, 2),
                "isa_temperature_c": round(isa, 2),
                "density_altitude_ft": round(da, 2),
                "classification": classification,
                "performance_impact": impact
            }
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/live")
def predict_live_weather(db: Session = Depends(get_db)):
    if temp_model is None or press_model is None:
        raise HTTPException(status_code=500, detail="Temperature/Pressure models are not loaded.")
        
    try:
        import requests
        # Fetch live data
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get('https://aviationweather.gov/api/data/metar?ids=VCBI&format=json', headers=headers, timeout=10)
        if response.status_code != 200 or not response.json():
            raise Exception("Failed to fetch live METAR data.")
            
        data = response.json()[0]
        
        # Parse data
        temp_c = data.get("temp", 30)
        dew_c = data.get("dewp", 25)
        wind_dir = data.get("wdir", 0)
        wind_spd = data.get("wspd", 0)
        visibility = data.get("visib")
        if isinstance(visibility, str) and '+' in visibility:
            visibility = float(visibility.replace('+', ''))
        elif visibility is None:
            visibility = 10.0
        else:
            visibility = float(visibility)
            
        qnh = data.get("altim", 1010)
        # Approximate Relative Humidity
        rh = 100 - 5 * (temp_c - dew_c) 
        
        clouds = ""
        if "clouds" in data and len(data["clouds"]) > 0:
            clouds = data["clouds"][0].get("cover", "")
            
        raw_ob = data.get("rawOb", "")
        
        obs_time = datetime.utcnow()
        if "reportTime" in data:
            try:
                # Format: 2026-08-19T18:10:00.000Z
                obs_time = datetime.strptime(data["reportTime"], "%Y-%m-%dT%H:%M:%S.%fZ")
            except:
                pass
                
        # Save to WeatherData
        weather_record = WeatherData(
            timestamp_utc=obs_time,
            year=obs_time.year,
            month=obs_time.month,
            date=obs_time.day,
            time_utc=obs_time.strftime("%H%M"),
            wind_dir=wind_dir,
            wind_speed_kts=wind_spd,
            visibility=visibility,
            weather=raw_ob,
            clouds=clouds,
            dry_temp_c=temp_c,
            dew_point_c=dew_c,
            rh_percent=rh,
            qnh_hpa=qnh
        )
        db.add(weather_record)
        db.commit()
        db.refresh(weather_record)
        
        # Run Prediction (now that live data is in DB)
        df = prepare_features_with_lags(db)
        
        X_temp = df.reindex(columns=temp_features, fill_value=0)
        X_temp_scaled = temp_scaler.transform(X_temp)
        predicted_temp = float(temp_model.predict(X_temp_scaled)[0])
        
        X_press = df.reindex(columns=press_features, fill_value=0)
        X_press_scaled = press_scaler.transform(X_press)
        predicted_press_diff = float(press_model.predict(X_press_scaled)[0])
        
        current_pressure = qnh
        predicted_press = current_pressure + predicted_press_diff
        
        try:
            seq = prepare_lstm_sequence(db)
            seq_scaled = lstm_scaler_X.transform(seq)
            seq_scaled = np.expand_dims(seq_scaled, axis=0)
            
            lstm_pred_scaled = lstm_model.predict(seq_scaled, verbose=0)
            lstm_pred = lstm_scaler_y.inverse_transform(lstm_pred_scaled)[0]
            
            curr_temp = seq[-1][0]
            curr_press = seq[-1][1]
            hybrid_features = np.array([[curr_temp, curr_press, lstm_pred[0], lstm_pred[1]]])
            
            final_pred = hybrid_model.predict(hybrid_features)[0]
            predicted_temp = float(final_pred[0])
            predicted_press = float(final_pred[1])
        except Exception as e:
            print("Hybrid failed, falling back to RF:", e)
            
        pa = calculate_pressure_altitude(predicted_press)
        isa = calculate_isa_temperature(pa)
        da = calculate_density_altitude(pa, predicted_temp, isa)
        classification = classify_vcbi_density_altitude(da)
        impact = get_aviation_performance_impact(classification)
        
        target_time = datetime.utcnow() + timedelta(hours=3)
        created_at_utc = datetime.utcnow()
        sl_tz_offset = timedelta(hours=5, minutes=30)
        
        record = TempPressurePredictionRecord(
            created_at=created_at_utc,
            forecast_type="3H_LIVE",
            target_year=target_time.year,
            target_month=target_time.month,
            target_date=target_time.day,
            target_time_utc=target_time.strftime("%H%M"),
            predicted_temperature_c=predicted_temp,
            predicted_pressure_hpa=predicted_press,
            status="SAFE"
        )
        db.add(record)
        
        from backend.data.models import ModelsForecast
        unified_record = ModelsForecast(
            target_time_utc=target_time,
            model_type='Temp_Press_3H_Live',
            temperature_c=predicted_temp,
            pressure_hpa=predicted_press
        )
        db.add(unified_record)
        
        db.commit()
        
        return {
            "live_data": {
                "temperature": temp_c,
                "pressure": qnh,
                "wind_speed": wind_spd,
                "wind_direction": wind_dir,
                "visibility": visibility,
                "time_utc": obs_time.strftime("%H%M"),
                "time_local": (obs_time + sl_tz_offset).strftime("%H%M"),
                "raw_ob": raw_ob
            },
            "prediction": {
                "temperature": round(predicted_temp, 2),
                "pressure": round(predicted_press, 2),
                "forecast_time_utc": target_time.strftime("%H%M"),
                "forecast_time_local": (target_time + sl_tz_offset).strftime("%H%M")
            },
            "derived_parameters": {
                "pressure_altitude_ft": round(pa, 2),
                "isa_temperature_c": round(isa, 2),
                "density_altitude_ft": round(da, 2),
                "classification": classification,
                "performance_impact": impact
            }
        }
        
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
