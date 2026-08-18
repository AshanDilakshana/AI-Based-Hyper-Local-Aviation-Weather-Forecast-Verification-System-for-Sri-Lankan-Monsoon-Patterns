from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import joblib
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import re
import urllib.request
import json
import threading
import time
import sqlite3

from database import (
    init_db, get_db_connection, save_observation, save_prediction, 
    verify_prediction, get_verification_history, get_latest_forecast, 
    get_recent_observations, save_briefing_package, get_briefing_packages,
    get_briefing_package_by_id
)

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)
DB_PATH = os.path.join(BASE_DIR, "weather_data.db")

# Load prediction objects for manual POST requests
try:
    temp_model = joblib.load(os.path.join(PROJECT_DIR, "model", "temp_model.pkl"))
    temp_scaler = joblib.load(os.path.join(PROJECT_DIR, "model", "temp_scaler.pkl"))
    temp_features = joblib.load(os.path.join(PROJECT_DIR, "model", "temp_feature_columns.pkl"))

    pressure_model = joblib.load(os.path.join(PROJECT_DIR, "model", "pressure_model.pkl"))
    pressure_scaler = joblib.load(os.path.join(PROJECT_DIR, "model", "pressure_scaler.pkl"))
    pressure_features = joblib.load(os.path.join(PROJECT_DIR, "model", "pressure_feature_columns.pkl"))
except Exception as e:
    print(f"Warning: Separate models not fully trained or found yet. Please run training script. Error: {e}")
    temp_model = None
    temp_scaler = None
    temp_features = []
    pressure_model = None
    pressure_scaler = None
    pressure_features = []

def make_prediction_for_obs(db_path, obs_data, dt, temp_model, temp_scaler, temp_features, pressure_model, pressure_scaler, pressure_features):
    # Prepare base dictionary
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
    
    # Retrieve past observations (retrieve 60 logs to cover up to lag 48)
    recent_obs = get_recent_observations(db_path, obs_data["obs_time"], limit=60)
    
    def get_lag_val(recent_list, lag_steps, key):
        idx = len(recent_list) - 1 - lag_steps
        if idx >= 0:
            return recent_list[idx][key]
        return obs_data[key]  # fallback
        
    # General lags for non-temperature variables (lags 1, 3, 6)
    for lag in [1, 3, 6]:
        df_dict[f"humidity_lag{lag}"] = get_lag_val(recent_obs, lag, "humidity")
        df_dict[f"pressure_lag{lag}"] = get_lag_val(recent_obs, lag, "pressure")
        df_dict[f"dew_point_lag{lag}"] = get_lag_val(recent_obs, lag, "dew_point")
        df_dict[f"wind_speed_lag{lag}"] = get_lag_val(recent_obs, lag, "wind_speed")
        df_dict[f"wind_direction_lag{lag}"] = get_lag_val(recent_obs, lag, "wind_direction")
        df_dict[f"visibility_lag{lag}"] = get_lag_val(recent_obs, lag, "visibility")
        
    # Additional temperature specific lags
    for lag in [1, 2, 3, 6, 12, 24, 48]:
        df_dict[f"temp_lag{lag}"] = get_lag_val(recent_obs, lag, "temperature")

    # Temperature gradients / differences
    df_dict["temp_diff_1"] = df_dict["temperature"] - df_dict["temp_lag1"]
    df_dict["temp_diff_2"] = df_dict["temperature"] - df_dict["temp_lag2"]
    df_dict["temp_diff_6"] = df_dict["temperature"] - df_dict["temp_lag6"]

    # Rolling calculations helper
    def get_roll_vals(recent_list, window, key):
        vals = []
        for i in range(window):
            idx = len(recent_list) - 1 - i
            if idx >= 0:
                vals.append(recent_list[idx][key])
        if len(vals) == 0:
            vals.append(obs_data[key])
        return vals
        
    # Rolling average features for other variables
    for window in [3, 6]:
        df_dict[f"humidity_roll{window}"] = np.mean(get_roll_vals(recent_obs, window, "humidity"))
        df_dict[f"pressure_roll{window}"] = np.mean(get_roll_vals(recent_obs, window, "pressure"))
        df_dict[f"dew_point_roll{window}"] = np.mean(get_roll_vals(recent_obs, window, "dew_point"))
        df_dict[f"wind_speed_roll{window}"] = np.mean(get_roll_vals(recent_obs, window, "wind_speed"))
        df_dict[f"visibility_roll{window}"] = np.mean(get_roll_vals(recent_obs, window, "visibility"))

    # Advanced temperature rolling statistics
    for window in [3, 6, 12, 24]:
        temp_vals = get_roll_vals(recent_obs, window, "temperature")
        df_dict[f"temp_roll{window}"] = np.mean(temp_vals)
        df_dict[f"temp_roll_std{window}"] = np.std(temp_vals) if len(temp_vals) > 1 else 0.0
        df_dict[f"temp_roll_min{window}"] = np.min(temp_vals)
        df_dict[f"temp_roll_max{window}"] = np.max(temp_vals)
        
    # Format into DataFrame matching temp_features ordering
    df_temp = pd.DataFrame([df_dict])
    for col in temp_features:
        if col not in df_temp.columns:
            df_temp[col] = 0
    df_temp = df_temp[temp_features].copy()
    df_temp_scaled = temp_scaler.transform(df_temp)
    pred_temp = temp_model.predict(df_temp_scaled)[0]

    # Format into DataFrame matching pressure_features ordering
    df_press = pd.DataFrame([df_dict])
    for col in pressure_features:
        if col not in df_press.columns:
            df_press[col] = 0
    df_press = df_press[pressure_features].copy()
    df_press_scaled = pressure_scaler.transform(df_press)
    pred_press = pressure_model.predict(df_press_scaled)[0]
    
    return float(pred_temp), float(pred_press)

def verify_past_predictions(db_path, obs_data):
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM predictions
        WHERE forecast_time = ? AND is_verified = 0
    """, (obs_data["obs_time"],))
    preds = cursor.fetchall()
    conn.close()
    
    for pred in preds:
        pred_id = pred["id"]
        pred_temp = pred["predicted_temperature"]
        pred_pressure = pred["predicted_pressure"]
        
        actual_temp = obs_data["temperature"]
        actual_pressure = obs_data["pressure"]
        
        temp_err = abs(actual_temp - pred_temp)
        pressure_err = abs(actual_pressure - pred_pressure)
        
        temp_status = "MATCH" if temp_err <= 2.0 else "MISMATCH"
        pressure_status = "MATCH" if pressure_err <= 3.0 else "MISMATCH"
        
        verify_prediction(
            db_path, pred_id, actual_temp, actual_pressure,
            temp_err, pressure_err, temp_status, pressure_status
        )

def run_and_save_prediction(db_path, obs_data, dt, temp_model, temp_scaler, temp_features, pressure_model, pressure_scaler, pressure_features):
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM predictions WHERE input_obs_time = ?", (obs_data["obs_time"],))
    exists = cursor.fetchone()
    conn.close()
    
    if exists:
        return
        
    pred_temp, pred_press = make_prediction_for_obs(
        db_path, obs_data, dt, 
        temp_model, temp_scaler, temp_features, 
        pressure_model, pressure_scaler, pressure_features
    )
    
    save_prediction(db_path, {
        "input_obs_time": obs_data["obs_time"],
        "forecast_time": obs_data["obs_time"] + 10800,  # +3 hours
        "predicted_temperature": round(pred_temp, 2),
        "predicted_pressure": round(pred_press, 2)
    })

def fetch_and_process_metar(db_path, temp_model, temp_scaler, temp_features, pressure_model, pressure_scaler, pressure_features):
    url = "https://aviationweather.gov/api/data/metar?ids=VCBI&format=json&hours=24"
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AeroMetAI-Sync"}
        )
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode())
    except Exception as e:
        print(f"Error fetching METAR data: {e}")
        return

    # Process observations sorted oldest to newest
    data = sorted(data, key=lambda x: x.get("obsTime", 0))
    for item in data:
        obs_time = item.get("obsTime")
        report_time_str = item.get("reportTime")
        if not obs_time or not report_time_str:
            continue
            
        report_time = report_time_str.replace("Z", "")
        
        temp = item.get("temp")
        dewp = item.get("dewp")
        altim = item.get("altim")
        wspd = item.get("wspd")
        wdir = item.get("wdir")
        raw_ob = item.get("rawOb", "")
        
        if temp is None or dewp is None or altim is None or wspd is None or wdir is None:
            continue
            
        # Compute relative humidity
        T = float(temp)
        Td = float(dewp)
        humidity = 100 * (np.exp((17.625 * Td) / (243.04 + Td)) / np.exp((17.625 * T) / (243.04 + T)))
        
        # Parse visibility
        visibility = None
        tokens = raw_ob.split()
        for token in tokens:
            if token == "CAVOK":
                visibility = 9999.0
                break
            if re.match(r"^\d{4}$", token):
                visibility = float(token)
                break
                
        if visibility is None:
            visib_str = str(item.get("visib", "6")).replace("+", "").strip()
            try:
                visib_val = float(visib_str)
                if visib_val <= 20:
                    visibility = 9999.0 if visib_val >= 6 else (visib_val * 1609.34)
                else:
                    visibility = visib_val
            except ValueError:
                visibility = 9999.0
                
        obs_data = {
            "obs_time": int(obs_time),
            "report_time": report_time,
            "temperature": float(temp),
            "humidity": float(humidity),
            "pressure": float(altim),
            "dew_point": float(dewp),
            "wind_speed": float(wspd),
            "wind_direction": float(wdir),
            "visibility": float(visibility),
            "raw_ob": raw_ob
        }
        
        save_observation(db_path, obs_data)
        verify_past_predictions(db_path, obs_data)
        
        dt = datetime.strptime(report_time[:19], "%Y-%m-%dT%H:%M:%S")
        if dt.hour % 3 == 0:
            run_and_save_prediction(
                db_path, obs_data, dt, 
                temp_model, temp_scaler, temp_features, 
                pressure_model, pressure_scaler, pressure_features
            )

def background_sync_worker(db_path):
    print("Background METAR sync thread started.")
    # Use globally loaded models to save RAM instead of loading a second copy
    t_model, t_scaler, t_features = temp_model, temp_scaler, temp_features
    p_model, p_scaler, p_features = pressure_model, pressure_scaler, pressure_features
    while True:
        try:
            print("Performing background weather data sync...")
            fetch_and_process_metar(
                db_path, 
                t_model, t_scaler, t_features, 
                p_model, p_scaler, p_features
            )
        except Exception as e:
            print(f"Error in weather sync thread loop: {e}")
        time.sleep(300)  # Polling interval: 5 minutes

# Manual API Prediction Route
@app.route("/predict", methods=["POST"])
def predict():
    data = request.json
    try:
        df = pd.DataFrame([{
            "temperature": float(data["temperature"]),
            "humidity": float(data["humidity"]),
            "pressure": float(data["pressure"]),
            "dew_point": float(data["dew_point"]),
            "wind_speed": float(data["wind_speed"]),
            "wind_direction": float(data["wind_direction"]),
            "visibility": float(data["visibility"])
        }])

        time_str = str(data.get("time_utc", "")).zfill(4)
        if len(time_str) != 4 or not time_str.isdigit():
            return jsonify({"error": "Invalid time_utc format. Use HHMM format, example: 0310"}), 400

        hour = int(time_str[:2])
        minute = int(time_str[2:])

        if hour > 23 or minute > 59:
            return jsonify({"error": "Invalid UTC time value"}), 400

        now = datetime.utcnow().replace(
            hour=hour, minute=minute, second=0, microsecond=0
        )

        df["hour"] = now.hour
        df["day"] = now.day
        df["month"] = now.month
        df["dayofweek"] = now.weekday()

        df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24)
        df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24)

        df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
        df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)

        df["wind_dir_sin"] = np.sin(2 * np.pi * df["wind_direction"] / 360)
        df["wind_dir_cos"] = np.cos(2 * np.pi * df["wind_direction"] / 360)

        df["dew_temp_spread"] = df["temperature"] - df["dew_point"]

        # Approximate lag features for one-off manual tests (non-temperature)
        for lag in [1, 3, 6]:
            df[f"humidity_lag{lag}"] = df["humidity"]
            df[f"pressure_lag{lag}"] = df["pressure"]
            df[f"dew_point_lag{lag}"] = df["dew_point"]
            df[f"wind_speed_lag{lag}"] = df["wind_speed"]
            df[f"wind_direction_lag{lag}"] = df["wind_direction"]
            df[f"visibility_lag{lag}"] = df["visibility"]

        # Temperature lags
        for lag in [1, 2, 3, 6, 12, 24, 48]:
            df[f"temp_lag{lag}"] = df["temperature"]

        # Temperature differences
        df["temp_diff_1"] = 0.0
        df["temp_diff_2"] = 0.0
        df["temp_diff_6"] = 0.0

        # Non-temperature rolling features
        for window in [3, 6]:
            df[f"humidity_roll{window}"] = df["humidity"]
            df[f"pressure_roll{window}"] = df["pressure"]
            df[f"dew_point_roll{window}"] = df["dew_point"]
            df[f"wind_speed_roll{window}"] = df["wind_speed"]
            df[f"visibility_roll{window}"] = df["visibility"]

        # Advanced temperature rolling statistics
        for window in [3, 6, 12, 24]:
            df[f"temp_roll{window}"] = df["temperature"]
            df[f"temp_roll_std{window}"] = 0.0
            df[f"temp_roll_min{window}"] = df["temperature"]
            df[f"temp_roll_max{window}"] = df["temperature"]

        # Format into DataFrame matching temp_features ordering
        df_temp = df.copy()
        for col in temp_features:
            if col not in df_temp.columns:
                df_temp[col] = 0
        df_temp = df_temp[temp_features].copy()
        df_temp_scaled = temp_scaler.transform(df_temp)
        pred_temp = temp_model.predict(df_temp_scaled)[0]

        # Format into DataFrame matching pressure_features ordering
        df_press = df.copy()
        for col in pressure_features:
            if col not in df_press.columns:
                df_press[col] = 0
        df_press = df_press[pressure_features].copy()
        df_press_scaled = pressure_scaler.transform(df_press)
        pred_press = pressure_model.predict(df_press_scaled)[0]

        return jsonify({
            "temperature": round(float(pred_temp), 2),
            "pressure": round(float(pred_press), 2),
            "forecast": "T+3 Hour Forecast",
            "input_time_utc": time_str,
            "forecast_time_utc": f"{(hour + 3) % 24:02d}{minute:02d}"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/verification-history", methods=["GET"])
def verification_history():
    try:
        history = get_verification_history(DB_PATH, limit=20)
        return jsonify(history)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/run-active-prediction", methods=["POST"])
def run_active_prediction():
    try:
        obs = get_recent_observations(DB_PATH, 2000000000, limit=1)
        if not obs or len(obs) == 0:
            return jsonify({"error": "No observations found in database to run prediction."}), 400
        
        latest_obs = obs[0]
        
        # Load model references
        t_model = joblib.load(os.path.join(PROJECT_DIR, "model", "temp_model.pkl"))
        t_scaler = joblib.load(os.path.join(PROJECT_DIR, "model", "temp_scaler.pkl"))
        t_features = joblib.load(os.path.join(PROJECT_DIR, "model", "temp_feature_columns.pkl"))
        
        p_model = joblib.load(os.path.join(PROJECT_DIR, "model", "pressure_model.pkl"))
        p_scaler = joblib.load(os.path.join(PROJECT_DIR, "model", "pressure_scaler.pkl"))
        p_features = joblib.load(os.path.join(PROJECT_DIR, "model", "pressure_feature_columns.pkl"))
        
        dt = datetime.strptime(latest_obs["report_time"][:19], "%Y-%m-%dT%H:%M:%S")
        
        # Check if already exists in predictions table
        conn = get_db_connection(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM predictions WHERE input_obs_time = ?", (latest_obs["obs_time"],))
        existing_pred = cursor.fetchone()
        conn.close()
        
        if existing_pred:
            pred_dict = dict(existing_pred)
            dt_out = dt + timedelta(hours=3)
            pred_dict["forecast_report_time"] = dt_out.strftime("%Y-%m-%dT%H:%M:%S")
            pred_dict["input_report_time"] = latest_obs["report_time"]
            return jsonify(pred_dict)
            
        pred_temp, pred_press = make_prediction_for_obs(
            DB_PATH, latest_obs, dt, 
            t_model, t_scaler, t_features, 
            p_model, p_scaler, p_features
        )
        
        pred_data = {
            "input_obs_time": latest_obs["obs_time"],
            "forecast_time": latest_obs["obs_time"] + 10800,  # +3 hours
            "predicted_temperature": round(pred_temp, 2),
            "predicted_pressure": round(pred_press, 2)
        }
        
        save_prediction(DB_PATH, pred_data)
        
        # Format string times for frontend render
        dt_out = dt + timedelta(hours=3)
        pred_data["forecast_report_time"] = dt_out.strftime("%Y-%m-%dT%H:%M:%S")
        pred_data["input_report_time"] = latest_obs["report_time"]
        
        return jsonify(pred_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/live-verification", methods=["GET"])
def live_verification():
    try:
        # Fetch live METAR
        url = "https://aviationweather.gov/api/data/metar?ids=VCBI&format=json"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            
        if not data:
            return jsonify({"error": "No live data available from AviationWeather"}), 404
            
        live_obs = data[0]
        live_temp = live_obs.get("temp")
        live_press = live_obs.get("altim")
        live_time_str = live_obs.get("reportTime") # e.g. "2026-08-17T21:40:00Z"
        
        # Convert string to timestamp
        dt = datetime.strptime(live_time_str[:19], "%Y-%m-%dT%H:%M:%S")
        live_timestamp = int(dt.timestamp())
        
        # Look for a prediction where the forecast_time is exactly for this hour
        # (Within a 3-hour window tolerance to find the closest prediction)
        conn = get_db_connection(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Find prediction that was forecasting for this live_timestamp (+/- 1.5 hours)
        cursor.execute('''
            SELECT * FROM predictions 
            WHERE forecast_time BETWEEN ? AND ?
            ORDER BY ABS(forecast_time - ?) ASC LIMIT 1
        ''', (live_timestamp - 5400, live_timestamp + 5400, live_timestamp))
        pred = cursor.fetchone()
        conn.close()
        
        if not pred:
            return jsonify({
                "status": "waiting",
                "live_time": live_time_str,
                "live_temp": live_temp,
                "live_press": live_press,
                "message": "No prediction found for the current hour. Wait for the model to generate forecasts."
            })
            
        pred_dict = dict(pred)
        pred_id = pred_dict["id"]
        pred_temp = pred_dict["predicted_temperature"]
        pred_press = pred_dict["predicted_pressure"]
        
        temp_error = round(pred_temp - live_temp, 2)
        press_error = round(pred_press - live_press, 2)
        
        # Calculate status
        abs_temp_err = abs(temp_error)
        if abs_temp_err <= 1.0:
            temp_status = "Excellent"
        elif abs_temp_err <= 2.5:
            temp_status = "Acceptable"
        else:
            temp_status = "Poor"
            
        abs_press_err = abs(press_error)
        if abs_press_err <= 1.0:
            press_status = "Excellent"
        elif abs_press_err <= 2.5:
            press_status = "Acceptable"
        else:
            press_status = "Poor"

        # Save verification to database if not already verified
        if pred_dict.get("is_verified") == 0:
            verify_prediction(
                DB_PATH, pred_id, live_temp, live_press, 
                temp_error, press_error, temp_status, press_status
            )
        
        return jsonify({
            "status": "success",
            "live_time": live_time_str,
            "live_temp": live_temp,
            "live_press": live_press,
            "predicted_temp": pred_temp,
            "predicted_press": pred_press,
            "temp_error": temp_error,
            "press_error": press_error
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/latest-forecast", methods=["GET"])
def latest_forecast():
    try:
        latest = get_latest_forecast(DB_PATH)
        if not latest:
            return jsonify({"error": "No forecasts found in database yet."}), 404
        
        # Calculate forecast_report_time (input_report_time + 3 hours)
        if "input_report_time" in latest and latest["input_report_time"]:
            try:
                dt_in = datetime.strptime(latest["input_report_time"][:19], "%Y-%m-%dT%H:%M:%S")
                dt_out = dt_in + timedelta(hours=3)
                latest["forecast_report_time"] = dt_out.strftime("%Y-%m-%dT%H:%M:%S")
            except Exception as e:
                print(f"Error calculating forecast time: {e}")
                latest["forecast_report_time"] = None
        else:
            latest["forecast_report_time"] = None

        # Fetch the corresponding input observation details
        conn = get_db_connection(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM observations WHERE obs_time = ?", (latest["input_obs_time"],))
        obs = cursor.fetchone()
        conn.close()
        
        return jsonify({
            "prediction": latest,
            "observation": dict(obs) if obs else None
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/sync-now", methods=["POST"])
def sync_now():
    try:
        fetch_and_process_metar(
            DB_PATH, 
            temp_model, temp_scaler, temp_features, 
            pressure_model, pressure_scaler, pressure_features
        )
        return jsonify({"status": "success", "message": "Manual sync completed."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/export-training-data", methods=["GET"])
def export_training_data():
    try:
        conn = get_db_connection(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM observations ORDER BY obs_time ASC")
        rows = cursor.fetchall()
        conn.close()
        
        # Build CSV file contents
        csv_data = "obs_time,report_time,temperature,humidity,pressure,dew_point,wind_speed,wind_direction,visibility\n"
        for r in rows:
            csv_data += f"{r['obs_time']},{r['report_time']},{r['temperature']},{r['humidity']},{r['pressure']},{r['dew_point']},{r['wind_speed']},{r['wind_direction']},{r['visibility']}\n"
            
        return Response(
            csv_data,
            mimetype="text/csv",
            headers={"Content-disposition": "attachment; filename=weather_training_dataset.csv"}
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/recent-observations", methods=["GET"])
def recent_observations():
    try:
        obs = get_recent_observations(DB_PATH, 2000000000, limit=10)
        return jsonify(obs)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/create-briefing", methods=["POST"])
def create_briefing():
    data = request.json
    try:
        dep_time = data.get("departure_time", "12:00")
        airport_code = str(data.get("airport_code", "VCBI")).upper().strip()
        area = str(data.get("area", "d")).lower().strip()
        flight_level = str(data.get("flight_level", "340")).strip()
        fly_hours = int(data.get("fly_hours", 6))
        lead_time = str(data.get("lead_time", "06")).strip()
        
        # Clean flight level to be 3 digits
        fl_val = flight_level.lower().replace("fl", "")
        if len(fl_val) < 3:
            fl_val = fl_val.zfill(3)
            
        # Format lead time as 2 digits
        if len(lead_time) < 2:
            lead_time = lead_time.zfill(2)
            
        filename = f"F{lead_time}_wind_{fl_val}_{area}.gif"
        
        # Create static/charts folder
        charts_dir = os.path.join(BASE_DIR, "static", "charts")
        os.makedirs(charts_dir, exist_ok=True)
        
        local_path = os.path.join(charts_dir, filename)
        chart_url = f"https://aviationweather.gov/data/products/fax/{filename}"
        
        # Download chart
        try:
            req = urllib.request.Request(
                chart_url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) WeatherSync"}
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                with open(local_path, "wb") as f:
                    f.write(response.read())
            local_url_path = f"/static/charts/{filename}"
        except Exception as e:
            print(f"Error downloading chart: {e}")
            # Fallback to local dummy placeholder
            local_url_path = "/static/charts/fallback.gif"
            fallback_filepath = os.path.join(charts_dir, "fallback.gif")
            if not os.path.exists(fallback_filepath):
                with open(fallback_filepath, "wb") as f:
                    f.write(b'GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;')
        
        # Fetch METAR
        metar_raw = ""
        try:
            metar_url = f"https://aviationweather.gov/api/data/metar?ids={airport_code}&format=json"
            req = urllib.request.Request(metar_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=8) as response:
                m_data = json.loads(response.read().decode())
                if m_data and len(m_data) > 0:
                    metar_raw = m_data[0].get("rawOb", "")
        except Exception as e:
            print(f"Error fetching METAR: {e}")
            
        if not metar_raw:
            metar_raw = f"METAR {airport_code} 071510Z 23010KT 9999 FEW018 29/24 Q1010 NOSIG"
            
        # Fetch TAF
        taf_raw = ""
        try:
            taf_url = f"https://aviationweather.gov/api/data/taf?ids={airport_code}&format=json"
            req = urllib.request.Request(taf_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=8) as response:
                t_data = json.loads(response.read().decode())
                if t_data and len(t_data) > 0:
                    taf_raw = t_data[0].get("rawTAF", "")
        except Exception as e:
            print(f"Error fetching TAF: {e}")
            
        if not taf_raw:
            taf_raw = f"TAF {airport_code} 071100Z 0712/0818 24009KT 9999 SCT018 TEMPO 0721/0800 5000 SHRA"
            
        # Save briefing package
        pkg = {
            "request_time": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "departure_time": dep_time,
            "airport_code": airport_code,
            "area": area.upper(),
            "flight_level": f"FL{fl_val}",
            "fly_hours": fly_hours,
            "metar_raw": metar_raw,
            "taf_raw": taf_raw,
            "chart_url": chart_url,
            "chart_file_path": local_url_path
        }
        
        pkg_id = save_briefing_package(DB_PATH, pkg)
        pkg["id"] = pkg_id
        
        return jsonify(pkg)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/briefings", methods=["GET"])
def get_all_briefings():
    try:
        pkgs = get_briefing_packages(DB_PATH, limit=20)
        return jsonify(pkgs)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Initialize SQLite database and background sync thread
init_db(DB_PATH)
sync_thread = threading.Thread(target=background_sync_worker, args=(DB_PATH,), daemon=True)
sync_thread.start()

if __name__ == "__main__":
    app.run(debug=True, port=5000)