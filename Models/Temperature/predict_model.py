import pandas as pd
import numpy as np
import joblib
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

model = joblib.load(os.path.join(BASE_DIR, "weather_model.pkl"))
scaler = joblib.load(os.path.join(BASE_DIR, "scaler.pkl"))
features = joblib.load(os.path.join(BASE_DIR, "feature_columns.pkl"))

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

now = datetime.utcnow()

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

df = df[features]

df_scaled = scaler.transform(df)
prediction = model.predict(df_scaled)

print("\n🌤️ T+3 Hour Prediction")
print("Temperature:", round(prediction[0][0], 2), "°C")
print("Pressure:", round(prediction[0][1], 2), "hPa")