import pandas as pd
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)

input_path = os.path.join(PROJECT_DIR, "data", "clean_northeast_monsoon.csv")
output_path = os.path.join(PROJECT_DIR, "data", "featured_northeast_monsoon.csv")

df = pd.read_csv(input_path)

df["datetime"] = pd.to_datetime(df["datetime"])
df = df.sort_values("datetime")

# Time features
df["hour"] = df["datetime"].dt.hour
df["day"] = df["datetime"].dt.day
df["month"] = df["datetime"].dt.month

# Lag features - main variables
df["temp_lag1"] = df["temperature"].shift(1)
df["humidity_lag1"] = df["humidity"].shift(1)
df["pressure_lag1"] = df["pressure"].shift(1)

# Lag features - extra factors
df["dew_point_lag1"] = df["dew_point"].shift(1)
df["wind_speed_lag1"] = df["wind_speed"].shift(1)
df["wind_direction_lag1"] = df["wind_direction"].shift(1)
df["visibility_lag1"] = df["visibility"].shift(1)

# Rolling average features - main variables
df["temp_roll3"] = df["temperature"].rolling(window=3).mean()
df["humidity_roll3"] = df["humidity"].rolling(window=3).mean()
df["pressure_roll3"] = df["pressure"].rolling(window=3).mean()

# Rolling average features - extra factors
df["dew_point_roll3"] = df["dew_point"].rolling(window=3).mean()
df["wind_speed_roll3"] = df["wind_speed"].rolling(window=3).mean()
df["visibility_roll3"] = df["visibility"].rolling(window=3).mean()

# T+3 future targets
df["target_temperature"] = df["temperature"].shift(-3)
df["target_humidity"] = df["humidity"].shift(-3)
df["target_pressure"] = df["pressure"].shift(-3)

df = df.dropna()

df.to_csv(output_path, index=False)

print("✅ Feature engineering completed!")
print("📁 Saved:", output_path)
print(df.head())
print("Shape:", df.shape)