import pandas as pd
import numpy as np

class FeatureEngineer:
    def __init__(self):
        pass

    def create_features(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        
        # Ensure sorting by datetime
        if "datetime" in df.columns:
            df["datetime"] = pd.to_datetime(df["datetime"])
            df = df.sort_values("datetime").reset_index(drop=True)
            
        # Basic time parameters
        if "datetime" in df.columns:
            df["hour"] = df["datetime"].dt.hour
            df["day"] = df["datetime"].dt.day
            df["month"] = df["datetime"].dt.month
            df["dayofweek"] = df["datetime"].dt.dayofweek
            
        # Cyclical time features
        if "hour" in df.columns:
            df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24)
            df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24)
        if "month" in df.columns:
            df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
            df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)
            
        # Wind direction cyclic features
        if "wind_direction" in df.columns:
            df["wind_dir_sin"] = np.sin(2 * np.pi * df["wind_direction"] / 360)
            df["wind_dir_cos"] = np.cos(2 * np.pi * df["wind_direction"] / 360)
            
        # Extra weather relationship feature
        if "temperature" in df.columns and "dew_point" in df.columns:
            df["dew_temp_spread"] = df["temperature"] - df["dew_point"]
            
        # Lag features
        for lag in [1, 3, 6]:
            for col in ["temperature", "humidity", "pressure", "dew_point", "wind_speed", "wind_direction", "visibility"]:
                if col in df.columns:
                    df[f"temp_lag{lag}" if col == "temperature" else f"{col}_lag{lag}"] = df[col].shift(lag)
                    
        # Rolling average features
        for window in [3, 6]:
            for col in ["temperature", "humidity", "pressure", "dew_point", "wind_speed", "visibility"]:
                if col in df.columns:
                    df[f"temp_roll{window}" if col == "temperature" else f"{col}_roll{window}"] = df[col].rolling(window=window).mean()
                    
        return df
