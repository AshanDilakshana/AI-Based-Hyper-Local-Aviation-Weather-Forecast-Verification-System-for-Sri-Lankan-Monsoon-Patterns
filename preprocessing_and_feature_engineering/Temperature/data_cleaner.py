import pandas as pd
import numpy as np

class DataCleaner:
    def __init__(self):
        self.column_mapping = {
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
        }
        self.numeric_cols = [
            "temperature",
            "humidity",
            "pressure",
            "dew_point",
            "wind_speed",
            "wind_direction",
            "visibility"
        ]

    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        
        # Rename columns if they exist
        df = df.rename(columns=self.column_mapping)
        df = df.drop(columns=["Unnamed: 14"], errors="ignore")
        
        # Format time_utc
        if "time_utc" in df.columns:
            df["time_utc"] = df["time_utc"].astype(str).str.replace(".0", "", regex=False).str.zfill(4)
            df["hour"] = df["time_utc"].str[:2].astype(int)
            df["minute"] = df["time_utc"].str[2:].astype(int)
        
        # Create datetime
        if all(col in df.columns for col in ["Year", "Month", "Date", "hour", "minute"]):
            df["datetime"] = pd.to_datetime(
                df["Year"].astype(str) + "-" +
                df["Month"].astype(str).str.zfill(2) + "-" +
                df["Date"].astype(str).str.zfill(2) + " " +
                df["hour"].astype(str).str.zfill(2) + ":" +
                df["minute"].astype(str).str.zfill(2),
                errors="coerce"
            )
        
        # Select required columns if they exist
        target_cols = [
            "datetime", "Month", "hour", "minute", 
            "temperature", "humidity", "pressure", "dew_point", 
            "wind_speed", "wind_direction", "visibility", "clouds", "weather"
        ]
        available_cols = [col for col in target_cols if col in df.columns]
        df = df[available_cols]
        
        # Convert numeric columns
        for col in self.numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
                
        # Clean categorical columns
        for col in ["clouds", "weather"]:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()
                
        # Filter for Northeast Monsoon months (Dec, Jan, Feb) if Month exists
        if "Month" in df.columns:
            df = df[df["Month"].isin([12, 1, 2])]
            
        df = df.dropna()
        df = df.drop_duplicates()
        
        if "datetime" in df.columns:
            df = df.sort_values("datetime").reset_index(drop=True)
            
        return df
