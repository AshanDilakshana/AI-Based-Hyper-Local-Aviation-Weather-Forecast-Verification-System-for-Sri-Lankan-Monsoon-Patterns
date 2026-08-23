import pandas as pd
import sys
import os

# Ensure backend modules can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from preprocessing_and_feature_engineering.wind_prediction_model.data_cleaner import DataCleaner
from preprocessing_and_feature_engineering.wind_prediction_model.feature_engineer import FeatureEngineer

class UnifiedWeatherPipeline:
    """
    Coordinator pipeline for Wind Speed Forecasting at any time horizon.
    """
    def __init__(self, forecast_hours: int):
        self.forecast_hours = forecast_hours
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
        
        # Dynamically set the target name based on the forecast hours
        self.target = f'Target_Wind_Speed_{self.forecast_hours}h_Ahead'

    def process_training_data(self, df: pd.DataFrame) -> tuple:
        """
        Runs the full pipeline for model training.
        Returns X (features) and y (target).
        """
        df_clean = self.cleaner.clean(df)
        df_features = self.engineer.create_features(df_clean)
        
        # Filter for Monsoon months (May to September)
        if 'Month' in df_features.columns:
            df_features = df_features[df_features['Month'].isin([5, 6, 7, 8, 9])]
            
            
        # --- THE CRITICAL SHIFT FOR FORECASTING ---
        # Data is in 30 min intervals. So shift rows = forecast_hours * 2
        row_shift = -(self.forecast_hours * 2)
        
        if 'Wind speed(Kts)' in df_features.columns:
            df_features[self.target] = df_features['Wind speed(Kts)'].shift(row_shift)
            
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
