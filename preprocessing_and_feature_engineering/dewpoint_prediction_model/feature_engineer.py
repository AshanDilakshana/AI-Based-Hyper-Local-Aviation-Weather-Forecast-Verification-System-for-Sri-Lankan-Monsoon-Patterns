import pandas as pd
import numpy as np

class DewpointFeatureEngineer:
    def __init__(self, data: pd.DataFrame):
        self.data = data.copy()

    def engineer_features(self, is_training: bool = True) -> pd.DataFrame:
        """
        Creates new features from existing meteorological data for Dewpoint prediction.
        """
        if 'timestamp_utc' not in self.data.columns:
            return self.data
            
        df = self.data.copy()
        
        # Time-based features
        df['hour'] = df['timestamp_utc'].dt.hour
        df['month'] = df['timestamp_utc'].dt.month
        df['day_of_year'] = df['timestamp_utc'].dt.dayofyear
        
        # Cyclical encoding
        df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
        df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
        df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
        df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)
        
        # Lag features for Dewpoint (t-1, t-2, t-3)
        if 'dew_point_c' in df.columns:
            df['dewpoint_lag_1'] = df['dew_point_c'].shift(1)
            df['dewpoint_lag_2'] = df['dew_point_c'].shift(2)
            df['dewpoint_lag_3'] = df['dew_point_c'].shift(3)
            
            # Rolling mean and std for Dewpoint
            df['dewpoint_rolling_mean_3h'] = df['dew_point_c'].rolling(window=3).mean()
            df['dewpoint_rolling_std_3h'] = df['dew_point_c'].rolling(window=3).std()

        # Lag features for related variables (Dry Temp)
        if 'dry_temp_c' in df.columns:
            df['dry_temp_lag_1'] = df['dry_temp_c'].shift(1)
            
        if is_training:
            # Target variable (predicting Dewpoint 3 hours ahead)
            if 'dew_point_c' in df.columns:
                df['target_dewpoint_3h'] = df['dew_point_c'].shift(-3)
            
            # Drop rows with NaN values resulting from shift/rolling operations
            df.dropna(inplace=True)
        else:
            # For inference, only drop NaNs in the features (first few rows), not the non-existent target
            subset = [c for c in df.columns if 'target' not in c]
            df.dropna(subset=subset, inplace=True)
        
        
        return df
