import pandas as pd
import numpy as np
import os

# Load raw Excel dataset
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)

file_path = os.path.join(PROJECT_DIR, "data", "bia_metar_data.xlsx")

df = pd.read_excel(file_path)

# Rename columns
df = df.rename(columns={
    "Dry tem(0C)": "temperature",
    "RH(%)": "humidity",
    "QNH (hPa)": "pressure",
    "Dew point(0C)": "dew_point",
    "Wind speed(Kts)": "wind_speed",
    "Wind Dir.": "wind_direction",
    "Visibility": "visibility",
    "Clouds": "clouds",
    "Weather": "weather",
    "Time(UTC)": "time_utc"
})

df = df.drop(columns=["Unnamed: 14"], errors="ignore")

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

# Select required columns
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
    "visibility",
    "clouds",
    "weather"
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

# Clean categorical columns
df["clouds"] = df["clouds"].astype(str).str.strip()
df["weather"] = df["weather"].astype(str).str.strip()

# Northeast Monsoon only: December, January, February
df = df[df["Month"].isin([12, 1, 2])]

# Remove invalid rows
df = df.dropna()
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

# Create T+3 hour future target
df["future_time"] = df["datetime"] + pd.Timedelta(hours=3)

future_df = df[[
    "datetime",
    "temperature",
    "pressure"
]].copy()

future_df = future_df.rename(columns={
    "datetime": "future_time",
    "temperature": "target_temperature",
    "pressure": "target_pressure"
})

df = df.merge(future_df, on="future_time", how="left")

# Remove rows without exact T+3 hour target
df = df.dropna(subset=["target_temperature", "target_pressure"])

# One-hot encode categorical columns
df = pd.get_dummies(df, columns=["clouds", "weather"], drop_first=True)

# Save final featured dataset
output_path = os.path.join(PROJECT_DIR, "data", "featured_northeast_monsoon.csv")
df.to_csv(output_path, index=False)

print("✅ Final preprocessing + T+3 target creation completed!")
print("📁 Saved:", output_path)
print("Shape:", df.shape)
print("Columns:", list(df.columns))
print(df.head())