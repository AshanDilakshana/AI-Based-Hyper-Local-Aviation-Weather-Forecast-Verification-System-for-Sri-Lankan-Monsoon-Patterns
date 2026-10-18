import pandas as pd
import numpy as np

class WeatherDataCleaner:
    def __init__(self):
        pass

    def clean_inference_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Cleans data for inference. Handles NaN replacement exactly like the training logic.
        """
        if df.empty:
            return df
            
        df_clean = df.copy()
        
        # Replace inf with nan
        df_clean = df_clean.replace([np.inf, -np.inf], np.nan)
        
        # Forward fill for time series
        df_clean = df_clean.ffill().bfill()
        df_clean = df_clean.fillna(0)
        
        return df_clean
