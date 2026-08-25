import os
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
import warnings
warnings.filterwarnings("ignore")

from pytorch_forecasting import TimeSeriesDataSet
from pytorch_forecasting.data import GroupNormalizer

def load_and_prepare_data(db_path):
    """
    Connects to the SQLite DB, fetches weather_data, and formats it for PyTorch Forecasting.
    """
    engine = create_engine(f"sqlite:///{db_path}")
    query = "SELECT * FROM weather_data ORDER BY id ASC"
    df = pd.read_sql(query, engine)
    
    # 1. Create a proper datetime index
    df['time_utc_str'] = df['time_utc'].astype(str).str.zfill(4)
    df['datetime'] = pd.to_datetime(
        df['year'].astype(str) + '-' + 
        df['month'].astype(str).str.zfill(2) + '-' + 
        df['date'].astype(str).str.zfill(2) + ' ' + 
        df['time_utc_str'].str[:2] + ':' + 
        df['time_utc_str'].str[2:],
        errors='coerce'
    )
    
    # Drop rows with invalid dates (e.g. Feb 29 on non-leap years)
    df = df.dropna(subset=['datetime'])
    
    # Sort chronologically
    df = df.sort_values('datetime').reset_index(drop=True)
    
    # Ensure uniform 1-hour intervals to fix mixed data issues 
    # (API provides hourly data at xx:10, but historical has 30-min data at xx:10 and xx:40)
    df = df[df['datetime'].dt.minute == 10].reset_index(drop=True)
    
    # 2. Add time index (continuous integer representing time steps)
    df['time_idx'] = df.index
    
    # 3. Add a dummy group column because TimeSeriesDataSet requires at least one group
    df['group'] = "VCBI_Station"
    
    # 4. Fill missing values (TFT cannot handle NaNs in targets/covariates)
    numeric_cols = ['wind_speed_kts', 'wind_dir', 'dry_temp_c', 'dew_point_c', 'rh_percent', 'qnh_hpa', 'visibility']
    for col in numeric_cols:
        df[col] = df[col].interpolate(method='linear').bfill().ffill()
    
    # 5. Extract categorical time features
    df['hour'] = df['datetime'].dt.hour.astype(str)
    df['month_cat'] = df['datetime'].dt.month.astype(str)
    
    # 6. Advanced Feature Engineering (Same as XGBoost Pipeline)
    # Wind Direction Encodings
    df['Wind Dir_Sin'] = np.sin(np.radians(df['wind_dir']))
    df['Wind Dir_Cos'] = np.cos(np.radians(df['wind_dir']))
    
    # Dew Point Depression
    df['Dew_Point_Depression'] = df['dry_temp_c'] - df['dew_point_c']
    
    # Hour Encodings (Cyclical)
    df['Hour_Sin'] = np.sin(2 * np.pi * df['datetime'].dt.hour / 24.0)
    df['Hour_Cos'] = np.cos(2 * np.pi * df['datetime'].dt.hour / 24.0)
    
    # Rolling Means and Lags (Dataset is now STRICTLY 1-Hour intervals)
    df['Wind_Speed_Rolling_Mean_6h'] = df['wind_speed_kts'].rolling(6, min_periods=1).mean()
    df['Wind speed(Kts)_lag_3h'] = df['wind_speed_kts'].shift(3).bfill()
    df['QNH_lag_3h'] = df['qnh_hpa'].shift(3).bfill()
    df['QNH_change_3h'] = df['qnh_hpa'] - df['QNH_lag_3h']
    
    return df

def create_tft_dataset(df, max_encoder_length=24, max_prediction_length=3):
    """
    Creates the TimeSeriesDataSet required for TFT training.
    max_encoder_length: How far back the model looks (e.g., 24 steps = 24 hours if hourly).
    max_prediction_length: How far forward it predicts (e.g., 3 steps = 3 hours).
    """
    # Define the dataset
    training_cutoff = df["time_idx"].max() - max_prediction_length
    
    training_dataset = TimeSeriesDataSet(
        df[lambda x: x.time_idx <= training_cutoff],
        time_idx="time_idx",
        target="wind_speed_kts",
        group_ids=["group"],
        min_encoder_length=max_encoder_length // 2,
        max_encoder_length=max_encoder_length,
        min_prediction_length=1,
        max_prediction_length=max_prediction_length,
        static_categoricals=["group"],
        time_varying_known_categoricals=["hour", "month_cat"],
        time_varying_known_reals=["time_idx", "Hour_Sin", "Hour_Cos"],
        time_varying_unknown_categoricals=[],
        time_varying_unknown_reals=[
            "wind_speed_kts", 
            "wind_dir", 
            "dry_temp_c", 
            "dew_point_c", 
            "rh_percent", 
            "qnh_hpa", 
            "visibility",
            "Wind Dir_Sin", 
            "Wind Dir_Cos", 
            "Dew_Point_Depression", 
            "Wind_Speed_Rolling_Mean_6h", 
            "Wind speed(Kts)_lag_3h", 
            "QNH_change_3h"
        ],
        target_normalizer=GroupNormalizer(
            groups=["group"], transformation="softplus"
        ),  # use softplus to ensure predictions are positive (wind speed can't be negative)
        add_relative_time_idx=True,
        add_target_scales=True,
        add_encoder_length=True,
    )
    
    return training_dataset

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.abspath(os.path.join(current_dir, '../../../weather_data.db'))
    
    print("Loading data from DB...")
    df = load_and_prepare_data(db_path)
    print(f"Data loaded. Shape: {df.shape}")
    
    print("Building TimeSeriesDataSet...")
    dataset = create_tft_dataset(df)
    print("TimeSeriesDataSet built successfully!")
