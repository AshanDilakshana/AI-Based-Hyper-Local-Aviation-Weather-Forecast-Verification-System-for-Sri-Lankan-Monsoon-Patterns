import pandas as pd

# Load raw Excel dataset
df = pd.read_excel("data/bia_metar_data.xlsx")

# Rename needed columns
df = df.rename(columns={
    "Dry tem(0C)": "temperature",
    "RH(%)": "humidity",
    "QNH (hPa)": "pressure",
    "Time(UTC)": "time_utc"
})

# Remove unused column
df = df.drop(columns=["Unnamed: 14"], errors="ignore")

# Create proper time format
df["time_utc"] = df["time_utc"].astype(str).str.zfill(4)

df["hour"] = df["time_utc"].str[:2].astype(int)
df["minute"] = df["time_utc"].str[2:].astype(int)

# Create datetime column
df["datetime"] = pd.to_datetime(
    df["Year"].astype(str) + "-" +
    df["Month"].astype(str) + "-" +
    df["Date"].astype(str) + " " +
    df["hour"].astype(str) + ":" +
    df["minute"].astype(str),
    errors="coerce"
)

# Select only your required columns
df = df[["datetime", "Month", "temperature", "humidity", "pressure"]]

# Convert to numeric
df["temperature"] = pd.to_numeric(df["temperature"], errors="coerce")
df["humidity"] = pd.to_numeric(df["humidity"], errors="coerce")
df["pressure"] = pd.to_numeric(df["pressure"], errors="coerce")

# Filter Northeast Monsoon: Dec, Jan, Feb
df = df[df["Month"].isin([12, 1, 2])]

# Clean
df = df.dropna()
df = df.drop_duplicates()
df = df.sort_values("datetime")

# Save clean dataset
df.to_csv("data/clean_northeast_monsoon.csv", index=False)

print("Preprocessing completed!")
print("Clean dataset saved: data/clean_northeast_monsoon.csv")
print(df.head())
print(df.shape)