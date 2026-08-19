from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import joblib
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List

router = APIRouter(prefix="/predict", tags=["Temperature & Pressure Forecast"])

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
        print("✅ Temperature and Pressure models loaded successfully.")
    except Exception as e:
        print(f"⚠️ Warning: Separate models not fully trained or found yet. Error: {e}")

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

# Database interaction helper
import sqlite3
def get_recent_observations(db_path, current_obs_time, limit=60):
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM weather_data WHERE obs_time < ? ORDER BY obs_time DESC LIMIT ?",
            (current_obs_time, limit)
        )
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows][::-1] # Reverse to get chronological order
    except Exception as e:
        print(f"Database error: {e}")
        return []

@router.post("/temp-press")
def predict_temperature_and_pressure(obs: ObservationRequest):
    """
    Predicts Temperature and Pressure 3 hours ahead using local random forest models.
    """
    if not temp_model or not pressure_model:
        raise HTTPException(status_code=503, detail="Models are not loaded.")

    try:
        obs_data = obs.dict()
        # Parse datetime
        dt = datetime.strptime(obs_data["report_time"][:19], "%Y-%m-%dT%H:%M:%S")

        df_dict = {
            "temperature": obs_data["temperature"],
            "humidity": obs_data["humidity"],
            "pressure": obs_data["pressure"],
            "dew_point": obs_data["dew_point"],
            "wind_speed": obs_data["wind_speed"],
            "wind_direction": obs_data["wind_direction"],
            "visibility": obs_data["visibility"],
            "hour": dt.hour,
            "day": dt.day,
            "month": dt.month,
            "dayofweek": dt.weekday(),
            "hour_sin": np.sin(2 * np.pi * dt.hour / 24),
            "hour_cos": np.cos(2 * np.pi * dt.hour / 24),
            "month_sin": np.sin(2 * np.pi * dt.month / 12),
            "month_cos": np.cos(2 * np.pi * dt.month / 12),
            "wind_dir_sin": np.sin(2 * np.pi * obs_data["wind_direction"] / 360),
            "wind_dir_cos": np.cos(2 * np.pi * obs_data["wind_direction"] / 360),
            "dew_temp_spread": obs_data["temperature"] - obs_data["dew_point"]
        }
        
        recent_obs = get_recent_observations(DB_PATH, obs_data["obs_time"], limit=60)
        
        def get_lag_val(recent_list, lag_steps, key):
            idx = len(recent_list) - 1 - lag_steps
            if idx >= 0:
                return recent_list[idx][key]
            return obs_data[key]
            
        for lag in [1, 3, 6]:
            df_dict[f"humidity_lag{lag}"] = get_lag_val(recent_obs, lag, "humidity")
            df_dict[f"pressure_lag{lag}"] = get_lag_val(recent_obs, lag, "pressure")
            df_dict[f"dew_point_lag{lag}"] = get_lag_val(recent_obs, lag, "dew_point")
            df_dict[f"wind_speed_lag{lag}"] = get_lag_val(recent_obs, lag, "wind_speed")
            df_dict[f"wind_direction_lag{lag}"] = get_lag_val(recent_obs, lag, "wind_direction")
            df_dict[f"visibility_lag{lag}"] = get_lag_val(recent_obs, lag, "visibility")
            
        for lag in [1, 2, 3, 6, 12, 24, 48]:
            df_dict[f"temp_lag{lag}"] = get_lag_val(recent_obs, lag, "temperature")

        df_dict["temp_diff_1"] = df_dict["temperature"] - df_dict["temp_lag1"]
        df_dict["temp_diff_2"] = df_dict["temperature"] - df_dict["temp_lag2"]
        df_dict["temp_diff_6"] = df_dict["temperature"] - df_dict["temp_lag6"]

        def get_roll_vals(recent_list, window, key):
            vals = []
            for i in range(window):
                idx = len(recent_list) - 1 - i
                if idx >= 0:
                    vals.append(recent_list[idx][key])
            if len(vals) == 0:
                vals.append(obs_data[key])
            return vals
            
        for window in [3, 6]:
            df_dict[f"humidity_roll{window}"] = np.mean(get_roll_vals(recent_obs, window, "humidity"))
            df_dict[f"pressure_roll{window}"] = np.mean(get_roll_vals(recent_obs, window, "pressure"))
            df_dict[f"dew_point_roll{window}"] = np.mean(get_roll_vals(recent_obs, window, "dew_point"))
            df_dict[f"wind_speed_roll{window}"] = np.mean(get_roll_vals(recent_obs, window, "wind_speed"))
            df_dict[f"visibility_roll{window}"] = np.mean(get_roll_vals(recent_obs, window, "visibility"))

        for window in [3, 6, 12, 24]:
            temp_vals = get_roll_vals(recent_obs, window, "temperature")
            df_dict[f"temp_roll{window}"] = np.mean(temp_vals)
            df_dict[f"temp_roll_std{window}"] = np.std(temp_vals) if len(temp_vals) > 1 else 0.0
            df_dict[f"temp_roll_min{window}"] = np.min(temp_vals)
            df_dict[f"temp_roll_max{window}"] = np.max(temp_vals)
            
        # Inference
        df_temp = pd.DataFrame([df_dict])
        for col in temp_features:
            if col not in df_temp.columns:
                df_temp[col] = 0
        df_temp = df_temp[temp_features].copy()
        df_temp_scaled = temp_scaler.transform(df_temp)
        pred_temp = temp_model.predict(df_temp_scaled)[0]

        df_press = pd.DataFrame([df_dict])
        for col in pressure_features:
            if col not in df_press.columns:
                df_press[col] = 0
        df_press = df_press[pressure_features].copy()
        df_press_scaled = pressure_scaler.transform(df_press)
        pred_press = pressure_model.predict(df_press_scaled)[0]

        dt_out = dt + timedelta(hours=3)

        return {
            "input_obs_time": obs_data["obs_time"],
            "forecast_time": obs_data["obs_time"] + 10800,
            "predicted_temperature": round(float(pred_temp), 2),
            "predicted_pressure": round(float(pred_press), 2),
            "forecast_report_time": dt_out.strftime("%Y-%m-%dT%H:%M:%S"),
            "input_report_time": obs_data["report_time"]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
