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

    history = pd.read_csv(history_path)
    history["datetime"] = pd.to_datetime(history["datetime"])
    history = history.sort_values("datetime")

    last_1 = history.tail(1)
    last_3 = history.tail(3)
    last_6 = history.tail(6)

    last_row = last_1.iloc[-1]

    # Lag features
    for lag, rows in [(1, last_1), (3, history.tail(3)), (6, history.tail(6))]:
        lag_row = rows.iloc[0]

        df[f"temp_lag{lag}"] = lag_row["temperature"]
        df[f"humidity_lag{lag}"] = lag_row["humidity"]
        df[f"pressure_lag{lag}"] = lag_row["pressure"]

        df[f"dew_point_lag{lag}"] = lag_row["dew_point"]
        df[f"wind_speed_lag{lag}"] = lag_row["wind_speed"]
        df[f"wind_direction_lag{lag}"] = lag_row["wind_direction"]
        df[f"visibility_lag{lag}"] = lag_row["visibility"]

    # Rolling features
    for window, rows in [(3, last_3), (6, last_6)]:
        df[f"temp_roll{window}"] = rows["temperature"].mean()
        df[f"humidity_roll{window}"] = rows["humidity"].mean()
        df[f"pressure_roll{window}"] = rows["pressure"].mean()

        df[f"dew_point_roll{window}"] = rows["dew_point"].mean()
        df[f"wind_speed_roll{window}"] = rows["wind_speed"].mean()
        df[f"visibility_roll{window}"] = rows["visibility"].mean()

    missing_cols = [col for col in features if col not in df.columns]

    if missing_cols:
        df_missing = pd.DataFrame(0, index=df.index, columns=missing_cols)
        df = pd.concat([df, df_missing], axis=1)

    df = df[features].copy()

    df_scaled = scaler.transform(df)
    prediction = model.predict(df_scaled)

    return jsonify({
        "temperature": round(float(prediction[0][0]), 2),
        "pressure": round(float(prediction[0][1]), 2)
    })


if __name__ == "__main__":
    app.run(debug=True)