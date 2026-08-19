import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'
os.environ['OMP_NUM_THREADS'] = '1'

import sys
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings("ignore")

# Make sure we can import the backend and TFT builder
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../'))
if project_root not in sys.path:
    sys.path.append(project_root)
    
sys.path.append(os.path.join(current_dir, 'TFT_3H'))

from TEmpory.TFT_3H.tft_dataset_builder import load_and_prepare_data

def get_latest_tft_checkpoint(lightning_logs_dir):
    if not os.path.exists(lightning_logs_dir):
        return None
    version_dirs = [d for d in os.listdir(lightning_logs_dir) if os.path.isdir(os.path.join(lightning_logs_dir, d)) and d.startswith("version_")]
    if not version_dirs:
        return None
    
    version_dirs.sort(key=lambda x: int(x.split('_')[1]))
    valid_versions = []
    for d in version_dirs:
        ckpt_dir = os.path.join(lightning_logs_dir, d, "checkpoints")
        if os.path.exists(ckpt_dir) and os.listdir(ckpt_dir):
            valid_versions.append(d)
            
    if not valid_versions:
        return None
        
    latest_version_dir = os.path.join(lightning_logs_dir, valid_versions[-1])
    checkpoints_dir = os.path.join(latest_version_dir, "checkpoints")
    return os.path.join(checkpoints_dir, os.listdir(checkpoints_dir)[0])

def run_hybrid_inference():
    print("==================================================")
    print("HYBRID MODEL PREDICTION: TFT_3H + XGBOOST_3H")
    print("==================================================")
    
    # ---------------------------------------------------------
    # 1. LOAD DATA
    # ---------------------------------------------------------
    db_path = os.path.join(project_root, 'weather_data.db')
    
    # TFT DataFrame (requires target series formatting)
    df_tft = load_and_prepare_data(db_path).tail(96).reset_index(drop=True)
    
    # XGBoost DataFrame (raw fetch for UnifiedWeatherPipeline)
    conn = sqlite3.connect(db_path)
    df_raw = pd.read_sql("SELECT * FROM weather_data ORDER BY id ASC", conn).tail(12)
    
    # Create the correct DataFrame format expected by XGBoost pipeline
    data = []
    for _, row in df_raw.iterrows():
        time_str = str(row['time_utc']).zfill(4)
        data.append({
            'Year': row['year'],
            'Month': row['month'],
            'Date': row['date'],
            'Time(UTC)': time_str,
            'Wind Dir': row['wind_dir'],
            'Wind speed(Kts)': row['wind_speed_kts'],
            'Dry Temp(0C)': row['dry_temp_c'],
            'Dew point(0C)': row['dew_point_c'],
            'RH(%)': row['rh_percent'],
            'QNH(hPa)': row['qnh_hpa']
        })
    df_xgb = pd.DataFrame(data)
    
    # ---------------------------------------------------------
    # 2. RUN XGBOOST PREDICTION (Run first to avoid Mac segfault)
    # ---------------------------------------------------------
    import xgboost as xgb
    from preprocessing_and_feature_engineering.wind_prediction_model.unified_pipeline import UnifiedWeatherPipeline
    
    xgb_path = os.path.join(project_root, 'Models/wind_models/3h prediction model/xgboost_wind_model_3h.json')
    xgb_model = xgb.XGBRegressor()
    xgb_model.load_model(xgb_path)
    print("Loading XGBoost 3H Model...")
    
    pipeline = UnifiedWeatherPipeline(forecast_hours=3)
    features = pipeline.process_inference_data(df_xgb)
    
    xgb_pred_value = float(xgb_model.predict(features[pipeline.required_features])[0])
    print(f"-> XGBoost 3H Prediction: {xgb_pred_value:.2f} Knots")
    
    # ---------------------------------------------------------
    # 3. RUN TFT PREDICTION
    # ---------------------------------------------------------
    import torch
    
    # pyrefly: ignore [missing-import]
    from pytorch_forecasting import TemporalFusionTransformer
    
    tft_logs_dir = os.path.join(current_dir, "TFT_3H", "lightning_logs")
    tft_ckpt = get_latest_tft_checkpoint(tft_logs_dir)
    
    if not tft_ckpt:
        print("TFT 3H model not found!")
        return
        
    print(f"Loading TFT Model from: {tft_ckpt.split('TEmpory/')[-1]}")
    tft_model = TemporalFusionTransformer.load_from_checkpoint(tft_ckpt)
    
    tft_preds = tft_model.predict(df_tft, mode="prediction", trainer_kwargs={"logger": False})
    tft_pred_value = tft_preds[0][2].item()
    print(f"-> TFT 3H Prediction    : {tft_pred_value:.2f} Knots")
    
    # ---------------------------------------------------------
    # 4. CALCULATE HYBRID PREDICTION (Average)
    # ---------------------------------------------------------
    hybrid_pred_value = (tft_pred_value + xgb_pred_value) / 2.0
    print("==================================================")
    print(f"⭐ HYBRID 3H PREDICTION: {hybrid_pred_value:.2f} Knots ⭐")
    print("==================================================")
    
    # ---------------------------------------------------------
    # 5. SAVE TO DATABASE FOR VERIFICATION
    # ---------------------------------------------------------
    try:
        last_row = df_tft.iloc[-1]
        time_str = str(last_row['time_utc']).zfill(4)
        dt = datetime(
            int(last_row['year']), 
            int(last_row['month']), 
            int(last_row['date']), 
            int(time_str[:2]), 
            int(time_str[2:])
        )
        dt_target = dt + timedelta(hours=3)
        
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO prediction_records 
            (forecast_type, target_year, target_month, target_date, target_time_utc, predicted_wind_speed_kts, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, ('HYBRID_3H', dt_target.year, dt_target.month, dt_target.day, dt_target.strftime("%H%M"), hybrid_pred_value, 'SAVED_VIA_INFERENCE', datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')))
        conn.commit()
        print(f"✅ Saved HYBRID_3H prediction for target time {dt_target.strftime('%Y-%m-%d %H:%M UTC')} to database!")
    except Exception as e:
        print(f"Failed to save to database: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    run_hybrid_inference()
