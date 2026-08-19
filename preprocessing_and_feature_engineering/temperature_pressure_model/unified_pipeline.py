import pandas as pd
import sys
import os

# Ensure backend modules can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from preprocessing_and_feature_engineering.temperature_pressure_model.data_cleaner import DataCleaner
from preprocessing_and_feature_engineering.temperature_pressure_model.feature_engineer import FeatureEngineer
import pickle

class UnifiedWeatherPipeline:
    """
    Coordinator pipeline for Temperature and Pressure Forecasting.
    """
    def __init__(self):
        self.cleaner = DataCleaner()
        self.engineer = FeatureEngineer()
        
        # Load required features from the pickle file to ensure exact matching
        base_dir = os.path.dirname(__file__)
        temp_features_path = os.path.abspath(os.path.join(base_dir, '../../../Models/Temperature/temp_feature_columns.pkl'))
        press_features_path = os.path.abspath(os.path.join(base_dir, '../../../Models/Temperature/pressure_feature_columns.pkl'))
        
        try:
            with open(temp_features_path, 'rb') as f:
                self.required_temp_features = pickle.load(f)
        except Exception as e:
            print(f"Warning: Could not load temp features, using defaults. Error: {e}")
            self.required_temp_features = []
            
        try:
            with open(press_features_path, 'rb') as f:
                self.required_press_features = pickle.load(f)
        except Exception as e:
            print(f"Warning: Could not load pressure features, using defaults. Error: {e}")
            self.required_press_features = []

    def process_inference_data(self, df_window: pd.DataFrame) -> tuple:
        """
        Runs the full pipeline for Live API Prediction.
        Returns the feature sets for Temperature and Pressure models.
        """
        df_clean = self.cleaner.clean(df_window)
        df_features = self.engineer.create_features(df_clean)
        
        # Get the latest row for inference
        latest_row = df_features.iloc[[-1]].copy()
        
        # Select required columns, fill missing with 0 if any
        temp_features = pd.DataFrame()
        press_features = pd.DataFrame()
        
        if self.required_temp_features:
            for col in self.required_temp_features:
                temp_features[col] = latest_row.get(col, 0)
                
        if self.required_press_features:
            for col in self.required_press_features:
                press_features[col] = latest_row.get(col, 0)

        return temp_features, press_features
