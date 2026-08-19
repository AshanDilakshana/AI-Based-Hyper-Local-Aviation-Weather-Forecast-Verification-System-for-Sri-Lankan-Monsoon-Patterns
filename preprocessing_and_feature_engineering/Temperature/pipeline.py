import pandas as pd
import numpy as np
from preprocessing_and_feature_engineering.data_cleaner import DataCleaner
from preprocessing_and_feature_engineering.feature_engineer import FeatureEngineer

class WeatherDataPipeline:
    def __init__(self):
        self.cleaner = DataCleaner()
        self.engineer = FeatureEngineer()
        self.targets = ["target_temperature", "target_pressure", "target_humidity"]

    def process_training_data(self, df: pd.DataFrame) -> tuple:
        """
        Cleans data, engineers features, generates targets, and splits into features and targets.
        """
        df_clean = self.cleaner.clean(df)
        df_features = self.engineer.create_features(df_clean)
        
        # Create T+3 hour future targets using exact datetime matching
        if "datetime" in df_features.columns:
            df_features["future_time"] = df_features["datetime"] + pd.Timedelta(hours=3)
            
            future_df = df_features[["datetime", "temperature", "pressure", "humidity"]].copy()
            future_df = future_df.rename(columns={
                "datetime": "future_time",
                "temperature": "target_temperature",
                "pressure": "target_pressure",
                "humidity": "target_humidity"
            })
            
            df_features = df_features.merge(future_df, on="future_time", how="left")
            
        # Drop rows without targets and drop rows that have NaN in features (due to lag/rolling)
        df_features = df_features.dropna(subset=self.targets)
        df_features = df_features.dropna()
        
        # Separate features and targets
        drop_cols = ["datetime", "future_time"] + self.targets
        X = df_features.drop(columns=drop_cols, errors="ignore")
        X = X.select_dtypes(include=[np.number])
        
        y = df_features[self.targets]
        
        return X, y

    def process_inference_data(self, df_window: pd.DataFrame, feature_columns=None) -> pd.DataFrame:
        """
        Cleans and engineers feature space for a live prediction window.
        """
        df_clean = self.cleaner.clean(df_window)
        df_features = self.engineer.create_features(df_clean)
        
        latest_row = df_features.iloc[[-1]].copy()
        
        # Drop non-feature columns
        drop_cols = ["datetime", "future_time"] + self.targets
        latest_row = latest_row.drop(columns=drop_cols, errors="ignore")
        latest_row = latest_row.select_dtypes(include=[np.number])
        
        if feature_columns is not None:
            # Conform to the expected feature list
            for col in feature_columns:
                if col not in latest_row.columns:
                    latest_row[col] = 0.0
            latest_row = latest_row[feature_columns]
            
        return latest_row
