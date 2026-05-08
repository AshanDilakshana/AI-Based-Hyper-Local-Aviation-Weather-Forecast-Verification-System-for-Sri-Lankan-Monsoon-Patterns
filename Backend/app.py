from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
import pandas as pd
import numpy as np
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)

model = joblib.load(os.path.join(PROJECT_DIR, "model", "weather_model.pkl"))
scaler = joblib.load(os.path.join(PROJECT_DIR, "model", "scaler.pkl"))
features = joblib.load(os.path.join(PROJECT_DIR, "model", "feature_columns.pkl"))


@app.route("/predict", methods=["POST"])
def predict():
    data = request.json

    df = pd.DataFrame([{
        "temperature": float(data["temperature"]),
        "humidity": float(data["humidity"]),
        "pressure": float(data["pressure"]),
        "dew_point": float(data["dew_point"]),
        "wind_speed": float(data["wind_speed"]),
        "wind_direction": float(data["wind_direction"]),
        "visibility": float(data["visibility"])
    }])

    # Use entered UTC time from frontend
    time_str = str(data.get("time_utc", "")).zfill(4)

    if len(time_str) != 4 or not time_str.isdigit():
        return jsonify({"error": "Invalid time_utc format. Use HHMM format, example: 0310"}), 400

    hour = int(time_str[:2])
    minute = int(time_str[2:])

    if hour > 23 or minute > 59:
        return jsonify({"error": "Invalid UTC time value"}), 400

    now = datetime.utcnow().replace(
        hour=hour,
        minute=minute,
        second=0,
        microsecond=0
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

    # For live single input, use current values as lag/rolling approximation
    for lag in [1, 3, 6]:
        df[f"temp_lag{lag}"] = df["temperature"]
        df[f"humidity_lag{lag}"] = df["humidity"]
        df[f"pressure_lag{lag}"] = df["pressure"]
        df[f"dew_point_lag{lag}"] = df["dew_point"]
        df[f"wind_speed_lag{lag}"] = df["wind_speed"]
        df[f"wind_direction_lag{lag}"] = df["wind_direction"]
        df[f"visibility_lag{lag}"] = df["visibility"]

    for window in [3, 6]:
        df[f"temp_roll{window}"] = df["temperature"]
        df[f"humidity_roll{window}"] = df["humidity"]
        df[f"pressure_roll{window}"] = df["pressure"]
        df[f"dew_point_roll{window}"] = df["dew_point"]
        df[f"wind_speed_roll{window}"] = df["wind_speed"]
        df[f"visibility_roll{window}"] = df["visibility"]

    for col in features:
        if col not in df.columns:
            df[col] = 0

    df = df[features].copy()

    df_scaled = scaler.transform(df)
    prediction = model.predict(df_scaled)

    return jsonify({
        "temperature": round(float(prediction[0][0]), 2),
        "pressure": round(float(prediction[0][1]), 2),
        "forecast": "T+3 Hour Forecast",
        "input_time_utc": time_str,
        "forecast_time_utc": f"{(hour + 3) % 24:02d}{minute:02d}"
    })


if __name__ == "__main__":
    app.run(debug=True)