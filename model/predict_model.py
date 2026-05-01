import joblib
import pandas as pd
from datetime import datetime

# Load model
model = joblib.load("model/weather_model.pkl")
scaler = joblib.load("model/scaler.pkl")
features = joblib.load("model/feature_columns.pkl")

# 👉 Example current weather (later frontend එකෙන් එනවා)
current_data = {
    "temperature": 28,
    "humidity": 80,
    "pressure": 1010
}

# Create dataframe
df = pd.DataFrame([current_data])

# Add time features
now = datetime.now()
df["hour"] = now.hour
df["day"] = now.day
df["month"] = now.month

# Dummy lag + rolling (initial version)
df["temp_lag1"] = df["temperature"]
df["humidity_lag1"] = df["humidity"]
df["pressure_lag1"] = df["pressure"]

df["temp_roll3"] = df["temperature"]
df["humidity_roll3"] = df["humidity"]
df["pressure_roll3"] = df["pressure"]

# Arrange columns
df = df[features]

# Scale
df_scaled = scaler.transform(df)

# Predict
prediction = model.predict(df_scaled)

print("\n🌤️ T+3 Hour Prediction:")
print("Temperature:", prediction[0][0])
print("Humidity:", prediction[0][1])
print("Pressure:", prediction[0][2])