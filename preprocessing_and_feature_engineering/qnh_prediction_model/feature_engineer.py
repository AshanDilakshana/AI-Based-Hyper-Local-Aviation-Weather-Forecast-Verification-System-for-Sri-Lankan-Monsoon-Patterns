import pandas as pd
import numpy as np

class QNHFeatureEngineer:
    def __init__(self, data: pd.DataFrame):
        self.data = data.copy()

    def engineer_features(self, is_training: bool = True) -> pd.DataFrame:
        """
        Creates new features from existing meteorological data.
        """
        if 'timestamp_utc' not in self.data.columns:
            return self.data
            
        df = self.data.copy()
        
        # Time-based features
        df['hour'] = df['timestamp_utc'].dt.hour
        
        # Cyclical encoding for hour (24 hours)
        df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
        df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
        
        # Temperature Spread (Dry Temp - Dewpoint)
        if 'dry_temp_c' in df.columns and 'dew_point_c' in df.columns:
            df['temp_spread'] = df['dry_temp_c'] - df['dew_point_c']
        
        # Lag features and Momentum for QNH assuming hourly data
        if 'qnh_hpa' in df.columns:
            df['qnh_lag_1'] = df['qnh_hpa'].shift(1)
            df['qnh_lag_2'] = df['qnh_hpa'].shift(2)
            
            # Momentum (Difference between current QNH and previous hour's QNH)
            df['qnh_momentum'] = df['qnh_hpa'] - df['qnh_lag_1']
            
            # Rolling means for QNH
            df['qnh_rolling_3'] = df['qnh_hpa'].rolling(window=3).mean()
            df['qnh_rolling_6'] = df['qnh_hpa'].rolling(window=6).mean()
        if is_training:
            # Target variable (predicting QNH 3 hours ahead)
            if 'qnh_hpa' in df.columns:
                df['target_qnh_3h'] = df['qnh_hpa'].shift(-3)
                
            # Drop rows with NaN values resulting from shift/rolling operations
            df.dropna(inplace=True)
        else:
            # For inference, only drop NaNs in the features, not the non-existent target
            subset = [c for c in df.columns if 'target' not in c]
            df.dropna(subset=subset, inplace=True)
        
        return df
