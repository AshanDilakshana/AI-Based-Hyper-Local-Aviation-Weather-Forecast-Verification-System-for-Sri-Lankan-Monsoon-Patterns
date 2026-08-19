import pandas as pd
import numpy as np
import os
import sqlite3

# Load raw database dataset
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)

db_path = os.path.join(PROJECT_DIR, "weather_data.db")
if not os.path.exists(db_path):
    raise FileNotFoundError(f"Database not found: {db_path}")

print(f"Connecting to database: {db_path}")
conn = sqlite3.connect(db_path)
df = pd.read_sql_query("SELECT * FROM weather_data", conn)
conn.close()

# Rename columns
df = df.rename(columns={
    "dry_temp_c": "temperature",
    "rh_percent": "humidity",
    "qnh_hpa": "pressure",
    "dew_point_c": "dew_point",
    "wind_speed_kts": "wind_speed",
    "wind_dir": "wind_direction",
    "year": "Year",
    "month": "Month",
    "date": "Date",
    "time_utc": "time_utc"
})

# Format time
df["time_utc"] = df["time_utc"].astype(str).str.replace(".0", "", regex=False).str.zfill(4)

df["hour"] = df["time_utc"].str[:2].astype(int)
df["minute"] = df["time_utc"].str[2:].astype(int)

# Create datetime
df["datetime"] = pd.to_datetime(
    df["Year"].astype(str) + "-" +
    df["Month"].astype(str).str.zfill(2) + "-" +
    df["Date"].astype(str).str.zfill(2) + " " +
    df["hour"].astype(str).str.zfill(2) + ":" +
    df["minute"].astype(str).str.zfill(2),
    errors="coerce"
)

# Select required columns (excluding clouds and weather strings to keep model feature counts optimal)
df = df[[
    "datetime",
    "Month",
    "hour",
    "minute",
    "temperature",
    "humidity",
    "pressure",
    "dew_point",
    "wind_speed",
    "wind_direction",
    "visibility"
]]

# Convert numeric columns
numeric_cols = [
    "temperature",
    "humidity",
    "pressure",
    "dew_point",
    "wind_speed",
    "wind_direction",
    "visibility"
]

for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Remove invalid/missing rows in the key features
df = df.dropna(subset=numeric_cols)
df = df.drop_duplicates()
df = df.sort_values("datetime").reset_index(drop=True)

# Time-based features
df["dayofweek"] = df["datetime"].dt.dayofweek

df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24)
df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24)

df["month_sin"] = np.sin(2 * np.pi * df["Month"] / 12)
df["month_cos"] = np.cos(2 * np.pi * df["Month"] / 12)

# Wind direction cyclic features
df["wind_dir_sin"] = np.sin(2 * np.pi * df["wind_direction"] / 360)
df["wind_dir_cos"] = np.cos(2 * np.pi * df["wind_direction"] / 360)

# Extra useful weather feature
df["dew_temp_spread"] = df["temperature"] - df["dew_point"]

# Save to clean dataset path for feature engineering script
output_path = os.path.join(PROJECT_DIR, "data", "clean_northeast_monsoon.csv")
os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_csv(output_path, index=False)

print("Preprocess from SQLite completed!")
print("Saved:", output_path)
print("Shape:", df.shape)
print("Columns:", list(df.columns))