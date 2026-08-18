import pandas as pd
import numpy as np
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)

input_path = os.path.join(PROJECT_DIR, "data", "clean_northeast_monsoon.csv")
output_path = os.path.join(PROJECT_DIR, "data", "featured_northeast_monsoon.csv")

df = pd.read_csv(input_path)

df["datetime"] = pd.to_datetime(df["datetime"])
df = df.sort_values("datetime").reset_index(drop=True)

# Time features
df["hour"] = df["datetime"].dt.hour
df["day"] = df["datetime"].dt.day
df["month"] = df["datetime"].dt.month
df["dayofweek"] = df["datetime"].dt.dayofweek

# Cyclical time features
df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24)
df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24)
df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)

# Wind direction cyclic features
df["wind_dir_sin"] = np.sin(2 * np.pi * df["wind_direction"] / 360)
df["wind_dir_cos"] = np.cos(2 * np.pi * df["wind_direction"] / 360)

# Extra weather relationship feature
df["dew_temp_spread"] = df["temperature"] - df["dew_point"]

# Lag features (General lags for all variables)
for lag in [1, 3, 6]:
    df[f"humidity_lag{lag}"] = df["humidity"].shift(lag)
    df[f"pressure_lag{lag}"] = df["pressure"].shift(lag)
    df[f"dew_point_lag{lag}"] = df["dew_point"].shift(lag)
    df[f"wind_speed_lag{lag}"] = df["wind_speed"].shift(lag)
    df[f"wind_direction_lag{lag}"] = df["wind_direction"].shift(lag)
    df[f"visibility_lag{lag}"] = df["visibility"].shift(lag)

# Additional temperature specific lags
for lag in [1, 2, 3, 6, 12, 24, 48]:
    df[f"temp_lag{lag}"] = df["temperature"].shift(lag)

# Temperature gradients / differences
df["temp_diff_1"] = df["temperature"] - df["temp_lag1"]  # 30 min change
df["temp_diff_2"] = df["temperature"] - df["temp_lag2"]  # 1 hour change
df["temp_diff_6"] = df["temperature"] - df["temp_lag6"]  # 3 hour change

# Rolling average features for other variables
for window in [3, 6]:
    df[f"humidity_roll{window}"] = df["humidity"].rolling(window=window).mean()
    df[f"pressure_roll{window}"] = df["pressure"].rolling(window=window).mean()
    df[f"dew_point_roll{window}"] = df["dew_point"].rolling(window=window).mean()
    df[f"wind_speed_roll{window}"] = df["wind_speed"].rolling(window=window).mean()
    df[f"visibility_roll{window}"] = df["visibility"].rolling(window=window).mean()

# Advanced temperature rolling statistics
for window in [3, 6, 12, 24]:
    df[f"temp_roll{window}"] = df["temperature"].rolling(window=window).mean()
    df[f"temp_roll_std{window}"] = df["temperature"].rolling(window=window).std()
    df[f"temp_roll_min{window}"] = df["temperature"].rolling(window=window).min()
    df[f"temp_roll_max{window}"] = df["temperature"].rolling(window=window).max()

# T+3 future targets using exact datetime matching
df["future_time"] = df["datetime"] + pd.Timedelta(hours=3)

future_df = df[["datetime", "temperature", "pressure"]].copy()

future_df = future_df.rename(columns={
    "datetime": "future_time",
    "temperature": "target_temperature",
    "pressure": "target_pressure"
})

df = df.merge(future_df, on="future_time", how="left")

# Remove rows without lag/rolling/target values
df = df.dropna()

df.to_csv(output_path, index=False)

print("Feature engineering + exact T+3 target creation completed!")
print("Saved:", output_path)
print(df.head())
print("Shape:", df.shape)