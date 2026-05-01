import pandas as pd
import os

# Load raw Excel dataset
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)

file_path = os.path.join(PROJECT_DIR, "data", "bia_metar_data.xlsx")

df = pd.read_excel(file_path)

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

df["time_utc"] = df["time_utc"].astype(str).str.zfill(4)

df["hour"] = df["time_utc"].str[:2].astype(int)
df["minute"] = df["time_utc"].str[2:].astype(int)

df["datetime"] = pd.to_datetime(
    df["Year"].astype(str) + "-" +
    df["Month"].astype(str) + "-" +
    df["Date"].astype(str) + " " +
    df["hour"].astype(str) + ":" +
    df["minute"].astype(str),
    errors="coerce"
)

df = df[[
    "datetime",
    "Month",
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

df["clouds"] = df["clouds"].astype(str)
df["weather"] = df["weather"].astype(str)

# Northeast Monsoon: Dec, Jan, Feb
df = df[df["Month"].isin([12, 1, 2])]

df = df.dropna()
df = df.drop_duplicates()
df = df.sort_values("datetime")

df = pd.get_dummies(df, columns=["clouds", "weather"], drop_first=True)

output_path = os.path.join(PROJECT_DIR, "data", "clean_northeast_monsoon.csv")
df.to_csv(output_path, index=False)

print("✅ Preprocessing completed!")
print("📁 Saved:", output_path)
print(df.head())
print("Shape:", df.shape)