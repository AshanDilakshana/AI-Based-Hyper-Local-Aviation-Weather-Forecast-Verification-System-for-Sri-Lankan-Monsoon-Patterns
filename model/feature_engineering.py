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

# Lag features
for lag in [1, 3, 6]:
    df[f"temp_lag{lag}"] = df["temperature"].shift(lag)
    df[f"humidity_lag{lag}"] = df["humidity"].shift(lag)
    df[f"pressure_lag{lag}"] = df["pressure"].shift(lag)
    df[f"dew_point_lag{lag}"] = df["dew_point"].shift(lag)
    df[f"wind_speed_lag{lag}"] = df["wind_speed"].shift(lag)
    df[f"wind_direction_lag{lag}"] = df["wind_direction"].shift(lag)
    df[f"visibility_lag{lag}"] = df["visibility"].shift(lag)

# Rolling average features
for window in [3, 6]:
    df[f"temp_roll{window}"] = df["temperature"].rolling(window=window).mean()
    df[f"humidity_roll{window}"] = df["humidity"].rolling(window=window).mean()
    df[f"pressure_roll{window}"] = df["pressure"].rolling(window=window).mean()
    df[f"dew_point_roll{window}"] = df["dew_point"].rolling(window=window).mean()
    df[f"wind_speed_roll{window}"] = df["wind_speed"].rolling(window=window).mean()
    df[f"visibility_roll{window}"] = df["visibility"].rolling(window=window).mean()

# T+3 future targets
df["target_temperature"] = df["temperature"].shift(-3)
df["target_pressure"] = df["pressure"].shift(-3)

df = df.dropna()

df.to_csv(output_path, index=False)

print("✅ Feature engineering completed!")
print("📁 Saved:", output_path)
print(df.head())
print("Shape:", df.shape)