import pandas as pd
import joblib
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)

model_path = os.path.join(PROJECT_DIR, "model", "weather_model.pkl")
scaler_path = os.path.join(PROJECT_DIR, "model", "scaler.pkl")
features_path = os.path.join(PROJECT_DIR, "model", "feature_columns.pkl")

model = joblib.load(model_path)
scaler = joblib.load(scaler_path)
features = joblib.load(features_path)

# Current input values
current_data = {
    "temperature": 20,
    "humidity": 45,
    "pressure": 1000,
    "dew_point": 12,
    "wind_speed": 8,
    "wind_direction": 60,
    "visibility": 10000,
}

df = pd.DataFrame([current_data])

now = datetime.now()

df["hour"] = now.hour
df["day"] = now.day
df["month"] = now.month

# Temporary lag values
df["temp_lag1"] = df["temperature"]
df["humidity_lag1"] = df["humidity"]
df["pressure_lag1"] = df["pressure"]

df["dew_point_lag1"] = df["dew_point"]
df["wind_speed_lag1"] = df["wind_speed"]
df["wind_direction_lag1"] = df["wind_direction"]
df["visibility_lag1"] = df["visibility"]

# Temporary rolling values
df["temp_roll3"] = df["temperature"]
df["humidity_roll3"] = df["humidity"]
df["pressure_roll3"] = df["pressure"]

df["dew_point_roll3"] = df["dew_point"]
df["wind_speed_roll3"] = df["wind_speed"]
df["visibility_roll3"] = df["visibility"]

# Add missing dummy columns from training
for col in features:
    if col not in df.columns:
        df[col] = 0

df = df[features]

df_scaled = scaler.transform(df)

prediction = model.predict(df_scaled)

print("\n🌤️ T+3 Hour Prediction")
print("Temperature:", round(prediction[0][0], 2), "°C")
print("Humidity:", round(prediction[0][1], 2), "%")
print("Pressure:", round(prediction[0][2], 2), "hPa")