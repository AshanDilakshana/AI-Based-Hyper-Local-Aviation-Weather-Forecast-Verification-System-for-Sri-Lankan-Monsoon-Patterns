import pandas as pd
import numpy as np
import warnings

warnings.filterwarnings('ignore')

class FeatureEngineer:
    """
    Handles the creation of new mathematical and time-based features from the cleaned data.
    """
    def __init__(self):
        pass

    def create_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Applies feature engineering: Circular encoding, Dew point depression, and Time Lags.
        Assumes data is already cleaned.
        """
        df_feat = df.copy()

        # 1. Trigonometric Encoding for Wind Direction
        if 'Wind Dir' in df_feat.columns:
            df_feat['Wind Dir_Sin'] = np.sin(np.radians(df_feat['Wind Dir']))
            df_feat['Wind Dir_Cos'] = np.cos(np.radians(df_feat['Wind Dir']))

        # 2. Dew Point Depression (Dry Air Factor)
        if 'Dry Temp(0C)' in df_feat.columns and 'Dew point(0C)' in df_feat.columns:
            df_feat['Dew_Point_Depression'] = df_feat['Dry Temp(0C)'] - df_feat['Dew point(0C)']

        # 3. Create Datetime Index for Time-based Lagging
        if all(c in df_feat.columns for c in ['Year', 'Month', 'Date', 'Time(UTC)']):
            # Time is usually in HHMM format as integer (e.g., 10 -> 0010)
            time_str = df_feat['Time(UTC)'].astype(str).str.zfill(4)
            try:
                df_feat['Datetime'] = pd.to_datetime(
                    df_feat['Year'].astype(str) + '-' +
                    df_feat['Month'].astype(str) + '-' +
                    df_feat['Date'].astype(str) + ' ' +
                    time_str.str[:2] + ':' + time_str.str[2:4],
                    errors='coerce'
                )
                df_feat.dropna(subset=['Datetime'], inplace=True)
                df_feat.sort_values('Datetime', inplace=True)
                df_feat.set_index('Datetime', inplace=True)
                
                # Create 3-hour lag feature for wind speed
                if 'Wind speed(Kts)' in df_feat.columns:
                    df_shifted = df_feat[['Wind speed(Kts)']].copy()
                    df_shifted.index = df_shifted.index + pd.Timedelta(hours=3)
                    df_shifted.columns = ['Wind speed(Kts)_lag_3h']
                    
                    df_feat = df_feat.join(df_shifted, how='left')
                
                df_feat.reset_index(inplace=True)
            except Exception as e:
                print(f"Warning: Datetime parsing failed during feature engineering: {e}")
                if 'Wind speed(Kts)' in df_feat.columns:
                    df_feat['Wind speed(Kts)_lag_3h'] = df_feat['Wind speed(Kts)'].shift(6)
        else:
             if 'Wind speed(Kts)' in df_feat.columns:
                    df_feat['Wind speed(Kts)_lag_3h'] = df_feat['Wind speed(Kts)'].shift(6)

        return df_feat
