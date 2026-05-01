from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
import pandas as pd
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)

model = joblib.load(os.path.join(PROJECT_DIR, "model", "weather_model.pkl"))
scaler = joblib.load(os.path.join(PROJECT_DIR, "model", "scaler.pkl"))
features = joblib.load(os.path.join(PROJECT_DIR, "model", "feature_columns.pkl"))

history_path = os.path.join(PROJECT_DIR, "data", "clean_northeast_monsoon.csv")


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

    now = datetime.now()
    df["hour"] = now.hour
    df["day"] = now.day
    df["month"] = now.month

    # Load real historical METAR data
    history = pd.read_csv(history_path)
    history["datetime"] = pd.to_datetime(history["datetime"])
    history = history.sort_values("datetime")

    last_row = history.iloc[-1]
    last_3 = history.tail(3)

    # Real lag values
    df["temp_lag1"] = last_row["temperature"]
    df["humidity_lag1"] = last_row["humidity"]
    df["pressure_lag1"] = last_row["pressure"]

    df["dew_point_lag1"] = last_row["dew_point"]
    df["wind_speed_lag1"] = last_row["wind_speed"]
    df["wind_direction_lag1"] = last_row["wind_direction"]
    df["visibility_lag1"] = last_row["visibility"]

    # Real rolling values
    df["temp_roll3"] = last_3["temperature"].mean()
    df["humidity_roll3"] = last_3["humidity"].mean()
    df["pressure_roll3"] = last_3["pressure"].mean()

    df["dew_point_roll3"] = last_3["dew_point"].mean()
    df["wind_speed_roll3"] = last_3["wind_speed"].mean()
    df["visibility_roll3"] = last_3["visibility"].mean()

    # Add missing encoded columns like clouds/weather dummy columns
    for col in features:
        if col not in df.columns:
            df[col] = 0

    df = df[features]

    df_scaled = scaler.transform(df)
    prediction = model.predict(df_scaled)

    return jsonify({
        "temperature": round(float(prediction[0][0]), 2),
        "humidity": round(float(prediction[0][1]), 2),
        "pressure": round(float(prediction[0][2]), 2)
    })


if __name__ == "__main__":
    app.run(debug=True)