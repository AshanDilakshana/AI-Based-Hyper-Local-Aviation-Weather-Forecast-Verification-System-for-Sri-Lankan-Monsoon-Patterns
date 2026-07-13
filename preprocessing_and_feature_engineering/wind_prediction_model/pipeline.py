import pandas as pd
from preprocessing_and_feature_engineering.wind_prediction_model.data_cleaner import DataCleaner
from preprocessing_and_feature_engineering.wind_prediction_model.feature_engineer import FeatureEngineer

class WeatherDataPipeline:
    """
    Main coordinator pipeline that runs data cleaning and then feature engineering.
    This acts as the bridge that orchestrates both files.
    """
    def __init__(self):
        self.cleaner = DataCleaner()
        self.engineer = FeatureEngineer()
        
        # The ultimate features we found via our Mutual Information analysis + Time of Day
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
        self.target = 'Target_Wind_Speed_1h_Ahead'

    def process_training_data(self, df: pd.DataFrame) -> tuple:
        """
        Runs the full pipeline for model training.
        Returns X (features) and y (target).
        """
        # Step 1: Preprocessing
        df_clean = self.cleaner.clean(df)
        
        # Step 2: Feature Engineering
        df_features = self.engineer.create_features(df_clean)
        
        # Filter for Monsoon months (May to September)
        if 'Month' in df_features.columns:
            df_features = df_features[df_features['Month'].isin([5, 6, 7, 8, 9])]
            
        # Shift target by 2 rows for 1-Hour ahead prediction (2 * 30 mins)
        if 'Wind speed(Kts)' in df_features.columns:
            df_features[self.target] = df_features['Wind speed(Kts)'].shift(-2)
            
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
        # Step 1: Preprocessing
        df_clean = self.cleaner.clean(df_window)
        
        # Step 2: Feature Engineering
        df_features = self.engineer.create_features(df_clean)
        
        latest_row = df_features.iloc[[-1]].copy()
        return latest_row[self.required_features]
