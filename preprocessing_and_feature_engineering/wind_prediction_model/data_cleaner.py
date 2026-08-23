import pandas as pd

class DataCleaner:
    """
    Handles all basic data preprocessing tasks:
    - Renaming columns to standard format
    - Coercing text/invalid data into numbers
    - Handling missing values (forward fill)
    """
    def __init__(self):
        # Mapping variations of column names to a standard format
        self.col_mapping = {
            'Wind Dir.': 'Wind Dir',
            'Dry tem(0C)': 'Dry Temp(0C)',
            'Dew point(0C)': 'Dew point(0C)', 
            'RH(%)': 'RH(%)',
            'QNH (hPa)': 'QNH(hPa)',
            'Wind speed(Kts)': 'Wind speed(Kts)',
            'Time(UTC)': 'Time(UTC)'
        }

    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Cleans the raw dataframe.
        """
        df_clean = df.copy()
        df_clean.rename(columns=self.col_mapping, inplace=True)

        # Convert Wind Dir to numeric, 'VRB' (Variable) becomes NaN
        if 'Wind Dir' in df_clean.columns:
            df_clean['Wind Dir'] = pd.to_numeric(df_clean['Wind Dir'], errors='coerce')
            
        # Ensure all other important columns are numeric
        numeric_cols = ['Wind speed(Kts)', 'Dry Temp(0C)', 'Dew point(0C)', 'RH(%)', 'QNH(hPa)']
        for col in numeric_cols:
            if col in df_clean.columns:
                df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
                
        # Forward fill to handle small gaps in continuous weather data before engineering features
        df_clean.ffill(inplace=True)
        return df_clean
