from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
import pandas as pd
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Load model once
model = joblib.load("model/weather_model.pkl")
scaler = joblib.load("model/scaler.pkl")
features = joblib.load("model/feature_columns.pkl")


@app.route("/predict", methods=["POST"])
def predict():
    data = request.json

    temperature = data["temperature"]
    humidity = data["humidity"]
    pressure = data["pressure"]

    df = pd.DataFrame([{
        "temperature": temperature,
        "humidity": humidity,
        "pressure": pressure
    }])

    now = datetime.now()

    df["hour"] = now.hour
    df["day"] = now.day
    df["month"] = now.month

    df["temp_lag1"] = df["temperature"]
    df["humidity_lag1"] = df["humidity"]
    df["pressure_lag1"] = df["pressure"]

    df["temp_roll3"] = df["temperature"]
    df["humidity_roll3"] = df["humidity"]
    df["pressure_roll3"] = df["pressure"]

    df = df[features]

    df_scaled = scaler.transform(df)
    prediction = model.predict(df_scaled)

    return jsonify({
        "temperature": float(prediction[0][0]),
        "humidity": float(prediction[0][1]),
        "pressure": float(prediction[0][2])
    })


if __name__ == "__main__":
    app.run(debug=True)