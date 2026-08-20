import os
import sqlite3
import pandas as pd
from .data_cleaner import QNHDataCleaner
from .feature_engineer import QNHFeatureEngineer

class QNHUnifiedPipeline:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def load_data(self) -> pd.DataFrame:
        """Loads data from the SQLite database."""
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"Database not found at {self.db_path}")
            
        conn = sqlite3.connect(self.db_path)
        query = "SELECT * FROM weather_data ORDER BY timestamp_utc"
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df

    def run_pipeline(self) -> pd.DataFrame:
        """Executes the full preprocessing and feature engineering pipeline."""
        print("Loading raw data from database...")
        df_raw = self.load_data()
        
        print("Cleaning data...")
        cleaner = QNHDataCleaner(df_raw)
        df_clean = cleaner.clean()
        
        print("Engineering features...")
        engineer = QNHFeatureEngineer(df_clean)
        df_features = engineer.engineer_features()
        
        print(f"Pipeline completed. Output shape: {df_features.shape}")
        return df_features
        
    def get_feature_columns(self, df: pd.DataFrame) -> list:
        """Returns the list of columns that are actually used as features by the model."""
        drop_cols = ['timestamp_utc', 'time_utc', 'weather', 'clouds', 'target_qnh_3h']
        return [c for c in df.columns if c not in drop_cols]

if __name__ == "__main__":
    # For testing the pipeline independently
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'weather_data.db')
    pipeline = QNHUnifiedPipeline(db_path)
    df_processed = pipeline.run_pipeline()
    print(df_processed.head())
