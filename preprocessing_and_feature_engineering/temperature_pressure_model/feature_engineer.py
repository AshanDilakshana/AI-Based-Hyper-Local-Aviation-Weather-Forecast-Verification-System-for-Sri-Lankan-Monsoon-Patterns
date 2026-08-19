import pandas as pd
import numpy as np
import warnings

warnings.filterwarnings('ignore')

class FeatureEngineer:
    def __init__(self):
        pass

    def create_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Applies feature engineering for Temperature and Pressure models.
        Assumes data is cleaned and columns are renamed.
        """
        df_feat = df.copy()

        # Parse Time
        if 'time_utc' in df_feat.columns:
            time_str = df_feat['time_utc'].astype(str).str.zfill(4)
            df_feat['hour'] = pd.to_numeric(time_str.str[:2], errors='coerce').fillna(0)
            df_feat['minute'] = pd.to_numeric(time_str.str[2:4], errors='coerce').fillna(0)
        else:
            df_feat['hour'] = 0
            df_feat['minute'] = 0

        # Rename for consistency if not done
        if 'Month' in df_feat.columns:
            df_feat['month'] = df_feat['Month']
        if 'Date' in df_feat.columns:
            df_feat['day'] = df_feat['Date']

        # Ensure datetime index for rolling/lag operations
        if all(c in df_feat.columns for c in ['Year', 'month', 'day', 'hour', 'minute']):
            try:
                df_feat['Datetime'] = pd.to_datetime(
                    df_feat['Year'].astype(str) + '-' +
                    df_feat['month'].astype(str) + '-' +
                    df_feat['day'].astype(str) + ' ' +
                    df_feat['hour'].astype(str).str.zfill(2) + ':' +
                    df_feat['minute'].astype(str).str.zfill(2),
                    errors='coerce'
                )
                df_feat.dropna(subset=['Datetime'], inplace=True)
                df_feat.sort_values('Datetime', inplace=True)
                df_feat.set_index('Datetime', inplace=True)
                df_feat['dayofweek'] = df_feat.index.dayofweek
            except Exception as e:
                print(f"Warning: Datetime parsing failed: {e}")
                df_feat['dayofweek'] = 0
        else:
            df_feat['dayofweek'] = 0

        # Trigonometric features
        df_feat['hour_sin'] = np.sin(2 * np.pi * df_feat['hour'] / 24.0)
        df_feat['hour_cos'] = np.cos(2 * np.pi * df_feat['hour'] / 24.0)
        if 'month' in df_feat.columns:
            df_feat['month_sin'] = np.sin(2 * np.pi * df_feat['month'] / 12.0)
            df_feat['month_cos'] = np.cos(2 * np.pi * df_feat['month'] / 12.0)
        else:
            df_feat['month_sin'] = 0
            df_feat['month_cos'] = 0
            
        if 'wind_direction' in df_feat.columns:
            df_feat['wind_dir_sin'] = np.sin(np.radians(df_feat['wind_direction']))
            df_feat['wind_dir_cos'] = np.cos(np.radians(df_feat['wind_direction']))

        if 'temperature' in df_feat.columns and 'dew_point' in df_feat.columns:
            df_feat['dew_temp_spread'] = df_feat['temperature'] - df_feat['dew_point']

        # Determine row shift for time lags. 
        # Assuming data is half-hourly, 1 hour = 2 rows. If hourly, 1 hour = 1 row.
        # We will assume 1 row = 1 hour for standard lags, 
        # or we can use time-based rolling/shifting if index is datetime.
        # Let's use simple row shifting since the model probably trained on sequential rows.
        # We will use row shifting where 1 step = 1 row (assuming hourly frequency for these features).
        
        # General lags
        for lag in [1, 3, 6]:
            for col in ['humidity', 'pressure', 'dew_point', 'wind_speed', 'wind_direction', 'visibility']:
                if col in df_feat.columns:
                    df_feat[f'{col}_lag{lag}'] = df_feat[col].shift(lag)
                    
        # Temp lags
        if 'temperature' in df_feat.columns:
            for lag in [1, 2, 3, 6, 12, 24, 48]:
                df_feat[f'temp_lag{lag}'] = df_feat['temperature'].shift(lag)
                
            # Temp diffs
            df_feat['temp_diff_1'] = df_feat['temperature'] - df_feat['temp_lag1']
            df_feat['temp_diff_2'] = df_feat['temperature'] - df_feat['temp_lag2']
            df_feat['temp_diff_6'] = df_feat['temperature'] - df_feat['temp_lag6']

        # General Rolling features
        for window in [3, 6]:
            for col in ['humidity', 'pressure', 'dew_point', 'wind_speed', 'visibility']:
                if col in df_feat.columns:
                    df_feat[f'{col}_roll{window}'] = df_feat[col].rolling(window, min_periods=1).mean()
                    
        # Temp Rolling features (mean, std, min, max)
        if 'temperature' in df_feat.columns:
            for window in [3, 6, 12, 24]:
                roll = df_feat['temperature'].rolling(window, min_periods=1)
                df_feat[f'temp_roll{window}'] = roll.mean()
                # fillna(0) for std because std of 1 item is NaN
                df_feat[f'temp_roll_std{window}'] = roll.std().fillna(0) 
                df_feat[f'temp_roll_min{window}'] = roll.min()
                df_feat[f'temp_roll_max{window}'] = roll.max()

        if 'Datetime' in df_feat.index.names:
            df_feat.reset_index(inplace=True)

        return df_feat
