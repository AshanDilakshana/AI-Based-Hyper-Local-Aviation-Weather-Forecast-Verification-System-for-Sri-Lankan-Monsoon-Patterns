import pandas as pd

class QNHDataCleaner:
    def __init__(self, data: pd.DataFrame):
        self.data = data.copy()

    def clean(self) -> pd.DataFrame:
        """
        Cleans the dataset by handling missing values and ensuring correct data types.
        """
        # Ensure timestamp is datetime
        if 'timestamp_utc' in self.data.columns:
            self.data['timestamp_utc'] = pd.to_datetime(self.data['timestamp_utc'], errors='coerce')
        
        # Sort values by time
        self.data.sort_values(by='timestamp_utc', inplace=True)
        
        # Drop rows where target variable (qnh_hpa) is missing
        if 'qnh_hpa' in self.data.columns:
            self.data.dropna(subset=['qnh_hpa'], inplace=True)
            
        # Handle missing values for other meteorological features
        numeric_cols = self.data.select_dtypes(include=['number']).columns
        # Forward fill and then backward fill for continuous time series data
        self.data[numeric_cols] = self.data[numeric_cols].ffill().bfill()
        
        return self.data





