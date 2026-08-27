import os
import sys
import pandas as pd
from datetime import datetime
import subprocess

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from backend.data.database import SessionLocal
from backend.data.models import WeatherData, SystemLogs



def get_all_historical_data(db_session):
    records = db_session.query(WeatherData).order_by(WeatherData.id.asc()).all()
    data = []
    for r in records:
        data.append({
            'Year': r.year,
            'Month': r.month,
            'Date': r.date,
            'Time(UTC)': str(r.time_utc).zfill(4) if r.time_utc else "0000",
            'Wind Dir': r.wind_dir,
            'Wind speed(Kts)': r.wind_speed_kts,
            'Dry Temp(0C)': r.dew_point_c, # Fixed mapping if dry_temp_c doesn't exist
            'Dew point(0C)': r.dew_point_c,
            'RH(%)': r.rh_percent,
            'QNH(hPa)': r.qnh_hpa
        })
    return pd.DataFrame(data)

def log_event(db_session, level, component, message, details=None):
    log = SystemLogs(level=level, component=component, message=message, details=details)
    db_session.add(log)
    db_session.commit()
    print(f"[{level}] {component}: {message}")



from backend.mlops_retrainer.sync_training_data import sync_training_data

def retrain_temperature_pressure():
    """
    Executes the training script for the Temperature and Pressure models
    and returns a tuple: (success_boolean, message, model_key).
    """
    # 0. Sync JIT Data
    sync_training_data()
    
    try:
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        train_lstm_script = os.path.join(BASE_DIR, "Models", "Temperature", "lstm_hybrid", "train_lstm_hybrid.py")
        train_rf_script = os.path.join(BASE_DIR, "Models", "Temperature", "random_forest", "train_quick_rf.py")
        
        print(f"Starting Temperature & Pressure Model Retraining...")
        
        # 1. Train LSTM Hybrid (Primary)
        print("Running train_lstm_hybrid.py...")
        result_lstm = subprocess.run(
            ["python", train_lstm_script], 
            capture_output=True, 
            text=True
        )
        
        # 2. Train Quick RF (Fallback)
        print("Running train_quick_rf.py...")
        result_rf = subprocess.run(
            ["python", train_rf_script], 
            capture_output=True, 
            text=True
        )
        
        model_key = "Temperature_Pressure_Model"
        msg = ""
        
        if result_lstm.returncode == 0 and result_rf.returncode == 0:
            if '--- HYBRID LSTM + RF PERFORMANCE ---' in result_lstm.stdout:
                metrics = result_lstm.stdout.split('--- HYBRID LSTM + RF PERFORMANCE ---')[-1].strip()
                msg = f"Retraining ran successfully. Details: {metrics}"
            else:
                msg = f"Retraining ran successfully."
            print(msg)
            return True, msg, model_key
        else:
            error_msg = f"Error retraining Models.\nLSTM Error: {result_lstm.stderr}\nRF Error: {result_rf.stderr}"
            print(error_msg)
            return False, error_msg, model_key
            
    except Exception as e:
        error_msg = f"Exception during Temperature/Pressure retraining: {str(e)}"
        print(error_msg)
        return False, error_msg, "Temperature_Pressure_Model"


def run_all_retrainings():
    final_results = {}
    
    success, msg, model_key = retrain_temperature_pressure()
    final_results[model_key] = msg
    
    return final_results

if __name__ == "__main__":
    results = run_all_retrainings()
    print("Retraining Results:", results)
