import pandas as pd
import numpy as np
from datetime import datetime

class WeatherFeatureEngineer:
    def __init__(self):
        pass
        
    def generate_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generates features for Temperature & Pressure prediction.
        Retains the exact logic from the original predict_model.py.
        """
        if df.empty:
            return df
            
        df_feat = df.copy()
        
        # In predict_model.py, time was taken as datetime.utcnow()
        # For historical inference (passing multiple rows), we'll use the latest timestamp, or extract from data if available.
        # But if 'hour' is not present, we can append it.
        if 'hour' not in df_feat.columns:
            now = datetime.utcnow()
            df_feat["hour"] = now.hour
            df_feat["day"] = now.day
            df_feat["month"] = now.month
            df_feat["dayofweek"] = now.weekday()
        
        # Trigonometric time features
        df_feat["hour_sin"] = np.sin(2 * np.pi * df_feat["hour"] / 24)
        df_feat["hour_cos"] = np.cos(2 * np.pi * df_feat["hour"] / 24)
        df_feat["month_sin"] = np.sin(2 * np.pi * df_feat["month"] / 12)
        df_feat["month_cos"] = np.cos(2 * np.pi * df_feat["month"] / 12)
        
        # Wind Direction trigonometric features
        if "wind_direction" in df_feat.columns:
            df_feat["wind_dir_sin"] = np.sin(2 * np.pi * df_feat["wind_direction"] / 360)
            df_feat["wind_dir_cos"] = np.cos(2 * np.pi * df_feat["wind_direction"] / 360)
            
        # Dew point spread
        if "temperature" in df_feat.columns and "dew_point" in df_feat.columns:
            df_feat["dew_temp_spread"] = df_feat["temperature"] - df_feat["dew_point"]
            
        # Lags
        # (In original predict_model.py, lags and rolls were just copies of the current row because it was a single row inference)
        # We will keep that exact behavior for single row inference, or actual shift if multiple rows.
        # To be completely safe and match the exact original logic for single row inference:
        for lag in [1, 3, 6]:
            if "temperature" in df_feat.columns: df_feat[f"temp_lag{lag}"] = df_feat["temperature"].shift(lag).fillna(df_feat["temperature"])
            if "humidity" in df_feat.columns: df_feat[f"humidity_lag{lag}"] = df_feat["humidity"].shift(lag).fillna(df_feat["humidity"])
            if "pressure" in df_feat.columns: df_feat[f"pressure_lag{lag}"] = df_feat["pressure"].shift(lag).fillna(df_feat["pressure"])
            if "dew_point" in df_feat.columns: df_feat[f"dew_point_lag{lag}"] = df_feat["dew_point"].shift(lag).fillna(df_feat["dew_point"])
            if "wind_speed" in df_feat.columns: df_feat[f"wind_speed_lag{lag}"] = df_feat["wind_speed"].shift(lag).fillna(df_feat["wind_speed"])
            if "wind_direction" in df_feat.columns: df_feat[f"wind_direction_lag{lag}"] = df_feat["wind_direction"].shift(lag).fillna(df_feat["wind_direction"])
            if "visibility" in df_feat.columns: df_feat[f"visibility_lag{lag}"] = df_feat["visibility"].shift(lag).fillna(df_feat["visibility"])
            
        for window in [3, 6]:
            if "temperature" in df_feat.columns: df_feat[f"temp_roll{window}"] = df_feat["temperature"].rolling(window=window, min_periods=1).mean()
            if "humidity" in df_feat.columns: df_feat[f"humidity_roll{window}"] = df_feat["humidity"].rolling(window=window, min_periods=1).mean()
            if "pressure" in df_feat.columns: df_feat[f"pressure_roll{window}"] = df_feat["pressure"].rolling(window=window, min_periods=1).mean()
            if "dew_point" in df_feat.columns: df_feat[f"dew_point_roll{window}"] = df_feat["dew_point"].rolling(window=window, min_periods=1).mean()
            if "wind_speed" in df_feat.columns: df_feat[f"wind_speed_roll{window}"] = df_feat["wind_speed"].rolling(window=window, min_periods=1).mean()
            if "visibility" in df_feat.columns: df_feat[f"visibility_roll{window}"] = df_feat["visibility"].rolling(window=window, min_periods=1).mean()

        return df_feat
