import pandas as pd

df = pd.read_csv("data/clean_northeast_monsoon.csv")

df["datetime"] = pd.to_datetime(df["datetime"])
df = df.sort_values("datetime")

# Time features
df["hour"] = df["datetime"].dt.hour
df["day"] = df["datetime"].dt.day
df["month"] = df["datetime"].dt.month

# Lag features
df["temp_lag1"] = df["temperature"].shift(1)
df["humidity_lag1"] = df["humidity"].shift(1)
df["pressure_lag1"] = df["pressure"].shift(1)

# Rolling average features
df["temp_roll3"] = df["temperature"].rolling(window=3).mean()
df["humidity_roll3"] = df["humidity"].rolling(window=3).mean()
df["pressure_roll3"] = df["pressure"].rolling(window=3).mean()

# T+3 future targets
df["target_temperature"] = df["temperature"].shift(-3)
df["target_humidity"] = df["humidity"].shift(-3)
df["target_pressure"] = df["pressure"].shift(-3)

df = df.dropna()

df.to_csv("data/featured_northeast_monsoon.csv", index=False)

print("Feature engineering completed!")
print("Saved: data/featured_northeast_monsoon.csv")
print(df.head())
print(df.shape)