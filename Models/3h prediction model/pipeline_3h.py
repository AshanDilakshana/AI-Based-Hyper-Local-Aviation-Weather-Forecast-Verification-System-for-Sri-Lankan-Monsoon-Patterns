import pandas as pd
import sys
import os

# Ensure backend modules can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from preprocessing_and_feature_engineering.data_cleaner import DataCleaner
from preprocessing_and_feature_engineering.feature_engineer import FeatureEngineer

class WeatherDataPipeline3H:
    """
    Coordinator pipeline for 3-Hour Forecasting.
    Shifts the target variable to predict the future.
    """
    def __init__(self):
        self.cleaner = DataCleaner()
        self.engineer = FeatureEngineer()
        
        self.required_features = [
            'Wind Dir_Sin', 
            'Wind Dir_Cos', 
            'Hour_Sin',
            'Hour_Cos',
            'Wind speed(Kts)_lag_3h', 
            'Dew_Point_Depression', 
            'Dry Temp(0C)', 
            'RH(%)',
            'QNH(hPa)',
            'QNH_change_3h',
            'Wind_Speed_Rolling_Mean_6h'
        ]
        self.target = 'Target_Wind_Speed_3h_Ahead'

    def process_training_data(self, df: pd.DataFrame) -> tuple:
        """
        Runs the full pipeline for 3h model training.
        """
        df_clean = self.cleaner.clean(df)
        df_features = self.engineer.create_features(df_clean)
        
        if 'Month' in df_features.columns:
            df_features = df_features[df_features['Month'].isin([5, 6, 7, 8, 9])]
            
        # --- THE CRITICAL SHIFT FOR 3H FORECAST ---
        # Shift the target variable UP by 6 rows (6 x 30 mins = 3 hours)
        # This aligns the CURRENT features with the FUTURE wind speed
        if 'Wind speed(Kts)' in df_features.columns:
            df_features[self.target] = df_features['Wind speed(Kts)'].shift(-6)
            
        required_cols = self.required_features + [self.target]
        available_cols = [c for c in required_cols if c in df_features.columns]
        df_final = df_features.dropna(subset=available_cols).copy()
        
        X = df_final[self.required_features]
        y = df_final[self.target]
        
        return X, y

    def process_inference_data(self, df_window: pd.DataFrame) -> pd.DataFrame:
        """
        Runs the full pipeline for Live API Prediction.
        """
        df_clean = self.cleaner.clean(df_window)
        df_features = self.engineer.create_features(df_clean)
        latest_row = df_features.iloc[[-1]].copy()
        return latest_row[self.required_features]
