import os
import torch
# pyrefly: ignore [missing-import]
from pytorch_forecasting import TemporalFusionTransformer
from tft_dataset_builder import load_and_prepare_data, create_tft_dataset

def run_inference():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    lightning_logs_dir = os.path.join(current_dir, "lightning_logs")
    if not os.path.exists(lightning_logs_dir):
        print(f"No trained model found at {lightning_logs_dir}. Please run train_tft_model.py first.")
        return
        
    version_dirs = [d for d in os.listdir(lightning_logs_dir) if os.path.isdir(os.path.join(lightning_logs_dir, d)) and d.startswith("version_")]
    if not version_dirs:
        print("No trained model versions found.")
        return
        
    # Sort by version number correctly (e.g. version_10 > version_2)
    version_dirs.sort(key=lambda x: int(x.split('_')[1]))
    
    # Filter only versions that actually have checkpoints
    valid_versions = []
    for d in version_dirs:
        ckpt_dir = os.path.join(lightning_logs_dir, d, "checkpoints")
        if os.path.exists(ckpt_dir) and os.listdir(ckpt_dir):
            valid_versions.append(d)
            
    if not valid_versions:
        print("No valid checkpoints found in any version directory.")
        return
        
    latest_version_dir = os.path.join(lightning_logs_dir, valid_versions[-1])
    checkpoints_dir = os.path.join(latest_version_dir, "checkpoints")
    
    best_model_path = os.path.join(checkpoints_dir, os.listdir(checkpoints_dir)[0])
    print(f"Loading best model from: {best_model_path}")
    
    best_tft = TemporalFusionTransformer.load_from_checkpoint(best_model_path)
    
    db_path = os.path.abspath(os.path.join(current_dir, '../../../weather_data.db'))
    df = load_and_prepare_data(db_path)
    
    # Take only the last 24 hours of data to speed up dataset building for single prediction
    df = df.tail(96).reset_index(drop=True)
    
    print("Running Prediction...")
    # Passing the dataframe directly to predict() automatically creates the future targets
    # and predicts the true unseen future step.
    predictions = best_tft.predict(df, mode="prediction", trainer_kwargs={"logger": False})
    predicted_speed = predictions[0][2].item()
    print("--------------------------------------------------")
    print(f"TFT Predicted Wind Speed (3H Ahead): {predicted_speed:.2f} Knots")
    print("--------------------------------------------------")
    
    # Save the prediction to the database for accuracy verification
    try:
        import sqlite3
        from datetime import datetime, timedelta
        
        # Calculate target time (3 hours ahead of the last data point)
        last_row = df.iloc[-1]
        time_str = str(last_row['time_utc']).zfill(4)
        dt = datetime(
            int(last_row['year']), 
            int(last_row['month']), 
            int(last_row['date']), 
            int(time_str[:2]), 
            int(time_str[2:])
        )
        dt_target = dt + timedelta(hours=3)
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Insert into prediction_records
        cursor.execute("""
            INSERT INTO prediction_records 
            (forecast_type, target_year, target_month, target_date, target_time_utc, predicted_wind_speed_kts, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, ('TFT_3H', dt_target.year, dt_target.month, dt_target.day, dt_target.strftime("%H%M"), predicted_speed, 'SAVED_VIA_INFERENCE', datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')))
        
        conn.commit()
        conn.close()
        print("✅ TFT 3H Prediction successfully saved to database for accuracy verification!")
    except Exception as e:
        print(f"Failed to save prediction to database: {e}")

if __name__ == "__main__":
    run_inference()
