import pandas as pd
import numpy as np
import warnings

warnings.filterwarnings('ignore')

class DataCleaner:
    def __init__(self):
        pass

    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Cleans the incoming data specifically for Temperature and Pressure models.
        Handles missing values and basic data type enforcement.
        """
        df_clean = df.copy()

        # Rename columns to standard names used by the model features if necessary
        rename_map = {
            'Dry Temp(0C)': 'temperature',
            'RH(%)': 'humidity',
            'QNH(hPa)': 'pressure',
            'Dew point(0C)': 'dew_point',
            'Wind speed(Kts)': 'wind_speed',
            'Wind Dir': 'wind_direction',
            'Time(UTC)': 'time_utc'
        }
        
        for old, new in rename_map.items():
            if old in df_clean.columns:
                df_clean.rename(columns={old: new}, inplace=True)

        # Forward fill and backward fill for any minor gaps
        df_clean.ffill(inplace=True)
        df_clean.bfill(inplace=True)
        
        # In case some columns like visibility are missing from the DB query, we need a fallback
        if 'visibility' not in df_clean.columns:
            df_clean['visibility'] = 10000.0  # Default good visibility if missing
            
        return df_clean
