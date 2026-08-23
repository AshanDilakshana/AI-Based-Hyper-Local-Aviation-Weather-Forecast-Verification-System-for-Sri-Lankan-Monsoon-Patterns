import pandas as pd
import joblib
import os

from .data_cleaner import WeatherDataCleaner
from .feature_engineer import WeatherFeatureEngineer

class UnifiedWeatherPipeline:
    def __init__(self, model_dir: str):
        self.cleaner = WeatherDataCleaner()
        self.engineer = WeatherFeatureEngineer()
        
        # Load features and scaler dynamically for inference
        self.features = joblib.load(os.path.join(model_dir, "feature_columns.pkl"))
        self.scaler = joblib.load(os.path.join(model_dir, "scaler.pkl"))
        
    def process_inference_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Processes real-time data for model inference exactly matching the training pipeline.
        """
        # 1. Clean the data
        df_cleaned = self.cleaner.clean_inference_data(df)
        
        # 2. Generate Features (Lags, Trigonometric, etc.)
        df_engineered = self.engineer.generate_features(df_cleaned)
        
        # 3. Ensure all feature columns expected by the model exist, fill with 0 if missing
        for col in self.features:
            if col not in df_engineered.columns:
                df_engineered[col] = 0
                
        # 4. Filter columns
        df_final = df_engineered[self.features]
        
        # 5. Scale features
        df_scaled_array = self.scaler.transform(df_final)
        
        # We can return as DataFrame for easy debugging/passing
        return df_scaled_array
