import os
import sys
import sqlite3
import joblib
import pandas as pd
from datetime import timedelta

# Add project root to path for imports
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '../../..'))
sys.path.append(PROJECT_ROOT)

from preprocessing_and_feature_engineering.qnh_prediction_model.unified_pipeline import QNHUnifiedPipeline

def run_manual_test():
    print("Running Manual Inference for QNH 3H Model...")
    
    db_path = os.path.join(PROJECT_ROOT, 'weather_data.db')
    pipeline = QNHUnifiedPipeline(db_path)
    
    # 1. Get processed data
    try:
        df = pipeline.run_pipeline()
    except Exception as e:
        print(f"Error in pipeline: {e}")
        return

    # 2. Get the latest available row for inference
    # Note: unified_pipeline shifts target_qnh_3h back. For real inference, 
    # we don't care about the target, just the current features.
    latest_row = df.iloc[[-1]].copy()
    
    # The actual time of the latest row before shift
    df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'])
    latest_timestamp = df['timestamp_utc'].iloc[-1]

    
    features = pipeline.get_feature_columns(df)
    
    X_latest = latest_row[features]
    
    # 3. Load Model
    model_path = os.path.join(SCRIPT_DIR, 'qnh_3h_lgbm.pkl')
    if not os.path.exists(model_path):
        print("Model not found. Please train it first.")
        return
        
    model = joblib.load(model_path)
    
    # 4. Predict
    prediction = model.predict(X_latest)[0]
    
    # Target time is latest timestamp + 3 hours
    target_time = latest_timestamp + timedelta(hours=3)
    
    print(f"Latest Data Time: {latest_timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"Target Time: {target_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"Predicted QNH: {prediction:.2f} hPa")
    
    # 5. Save to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO dewpoint_qnh_predictions (target_time_utc, model_type, predicted_value, status)
        VALUES (?, ?, ?, ?)
    ''', (target_time.strftime('%Y-%m-%d %H:%M:%S'), 'QNH_3H', prediction, 'PENDING LIVE DATA'))
    conn.commit()
    conn.close()
    
    print("Prediction saved to database successfully.")

if __name__ == "__main__":
    run_manual_test()
