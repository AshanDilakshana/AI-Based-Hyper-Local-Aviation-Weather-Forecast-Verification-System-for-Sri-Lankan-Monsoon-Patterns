import os
import sqlite3
import pandas as pd
from .data_cleaner import DewpointDataCleaner
from .feature_engineer import DewpointFeatureEngineer

class DewpointUnifiedPipeline:
    def __init__(self, db_path: str = None, engine=None):
        self.db_path = db_path
        self.engine = engine

    def load_data(self, is_training: bool = True) -> pd.DataFrame:
        """Loads data from the database. For inference, fetches only the latest records."""
        if is_training:
            query = "SELECT * FROM weather_data ORDER BY timestamp_utc"
        else:
            query = "SELECT * FROM (SELECT * FROM weather_data ORDER BY timestamp_utc DESC LIMIT 100) ORDER BY timestamp_utc ASC"

        if self.engine is not None:
            try:
                df = pd.read_sql_query(query, self.engine)
            except Exception as e:
                # Fallback to local SQLite if remote engine connection fails or drops SSL
                if self.db_path and os.path.exists(self.db_path):
                    conn = sqlite3.connect(self.db_path)
                    df = pd.read_sql_query(query, conn)
                    conn.close()
                else:
                    raise e
        else:
            if not os.path.exists(self.db_path):
                raise FileNotFoundError(f"Database not found at {self.db_path}")
                
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query(query, conn)
            conn.close()
        return df

    def run_pipeline(self, is_training: bool = True) -> pd.DataFrame:
        """Executes the full preprocessing and feature engineering pipeline."""
        print("Loading raw data from database...")
        df_raw = self.load_data(is_training=is_training)
        
        print("Cleaning data...")
        cleaner = DewpointDataCleaner(df_raw)
        df_clean = cleaner.clean()
        
        print("Engineering features...")
        engineer = DewpointFeatureEngineer(df_clean)
        df_features = engineer.engineer_features(is_training=is_training)
        
        print(f"Pipeline completed. Output shape: {df_features.shape}")
        return df_features
        
    def get_feature_columns(self, df: pd.DataFrame) -> list:
        """Returns the list of columns that are actually used as features by the model."""
        drop_cols = ['timestamp_utc', 'time_utc', 'weather', 'clouds', 'target_dewpoint_3h']
        return [c for c in df.columns if c not in drop_cols]

if __name__ == "__main__":
    # For testing the pipeline independently
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'weather_data.db')
    pipeline = DewpointUnifiedPipeline(db_path)
    df_processed = pipeline.run_pipeline()
    print(df_processed.head())
