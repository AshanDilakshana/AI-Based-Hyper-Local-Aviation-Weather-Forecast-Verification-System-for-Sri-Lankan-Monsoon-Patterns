import os
import sys
import joblib
import pandas as pd
import lightgbm as lgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
import sqlite3
from datetime import datetime
import shutil

# Add project root to path for imports
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '../..'))
sys.path.append(PROJECT_ROOT)

from preprocessing_and_feature_engineering.dewpoint_prediction_model.unified_pipeline import DewpointUnifiedPipeline

def log_retraining_to_db(db_path, model_name, old_mae, new_mae, status, timestamp):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS model_retraining_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                model_name TEXT,
                old_mae REAL,
                new_mae REAL,
                status TEXT
            )
        ''')
        cursor.execute('''
            INSERT INTO model_retraining_logs (timestamp, model_name, old_mae, new_mae, status)
            VALUES (?, ?, ?, ?, ?)
        ''', (timestamp, model_name, old_mae, new_mae, status))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Failed to log retraining to database: {e}")

def train_dewpoint_3h_model():
    print("Starting Dewpoint 3H Prediction Model Training...")
    
    db_path = os.path.join(PROJECT_ROOT, 'weather_data.db')
    pipeline = DewpointUnifiedPipeline(db_path)
    
    # Get processed data
    try:
        df = pipeline.run_pipeline()
    except Exception as e:
        print(f"Error in pipeline: {e}")
        return

    # Define features and target
    features = pipeline.get_feature_columns(df)
    
    X = df[features]
    y = df['target_dewpoint_3h']
    
    # Train-test split (time series split: no shuffle)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)
    
    print(f"Training Data Shape: {X_train.shape}")
    print(f"Testing Data Shape: {X_test.shape}")
    
    # LightGBM Model
    print("Training LightGBM Regressor (New Model)...")
    new_model = lgb.LGBMRegressor(n_estimators=1000, learning_rate=0.01, num_leaves=31, random_state=42)
    new_model.fit(X_train, y_train)
    
    # Evaluate New Model
    new_preds = new_model.predict(X_test)
    new_mae = mean_absolute_error(y_test, new_preds)
    
    print(f"New Model MAE: {new_mae:.4f}")
    
    # Model Promotion Logic
    model_path = os.path.join(SCRIPT_DIR, 'dewpoint_3h_lgbm.pkl')
    backup_path = os.path.join(SCRIPT_DIR, 'dewpoint_3h_lgbm_backup.pkl')
    assets_path = os.path.join(SCRIPT_DIR, 'dewpoint_3h_test_assets.pkl')
    
    old_mae = None
    promotion_status = "Promoted (First Time)"
    
    if os.path.exists(model_path):
        print("Existing model found. Evaluating old model...")
        try:
            old_model = joblib.load(model_path)
            old_preds = old_model.predict(X_test)
            old_mae = mean_absolute_error(y_test, old_preds)
            print(f"Old Model MAE: {old_mae:.4f}")
            
            if new_mae <= old_mae:
                print("New model is BETTER or EQUAL. Promoting new model and backing up the old one.")
                shutil.copy2(model_path, backup_path)
                joblib.dump(new_model, model_path)
                joblib.dump((X_test, y_test, features), assets_path)
                promotion_status = "Promoted (Better or Equal MAE)"
            else:
                print("New model is WORSE. Discarding new model.")
                promotion_status = "Discarded (Worse MAE)"
        except Exception as e:
            print(f"Error loading/evaluating old model: {e}. Overwriting anyway.")
            shutil.copy2(model_path, backup_path) if os.path.exists(model_path) else None
            joblib.dump(new_model, model_path)
            joblib.dump((X_test, y_test, features), assets_path)
            promotion_status = "Promoted (Old Model Corrupted)"
    else:
        print("No existing model found. Saving as primary model.")
        joblib.dump(new_model, model_path)
        joblib.dump((X_test, y_test, features), assets_path)
    
    # Log to Database
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_retraining_to_db(db_path, "Dewpoint_3H", old_mae, new_mae, promotion_status, timestamp)
    print(f"Retraining complete. Status: {promotion_status}")

if __name__ == "__main__":
    train_dewpoint_3h_model()
