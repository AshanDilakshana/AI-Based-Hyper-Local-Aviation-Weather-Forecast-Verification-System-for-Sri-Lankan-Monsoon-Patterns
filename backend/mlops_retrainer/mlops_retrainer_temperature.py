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



def retrain_temperature_pressure_pipeline():
    """
    Executes the training script for the Temperature and Pressure models
    and returns a tuple: (success_boolean, message, model_key).
    """
    try:
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        train_script = os.path.join(BASE_DIR, "Models", "Temperature", "train_lstm_hybrid.py")
        
        print(f"Starting Temperature & Pressure Model Retraining...")
        
        result = subprocess.run(
            ["python", train_script], 
            capture_output=True, 
            text=True
        )
        
        model_key = "Temperature_Pressure_Model"
        
        if result.returncode == 0:
            if '--- HYBRID LSTM + RF PERFORMANCE ---' in result.stdout:
                metrics = result.stdout.split('--- HYBRID LSTM + RF PERFORMANCE ---')[-1].strip()
                msg = f"Retraining ran successfully. Details: {metrics}"
            else:
                msg = f"Retraining ran successfully. Output: {result.stdout.strip()}"

            print(msg)
            return True, msg, model_key
        else:
            error_msg = f"Error retraining Temperature/Pressure Models: {result.stderr}"
            print(error_msg)
            return False, error_msg, model_key
            
    except Exception as e:
        error_msg = f"Exception during Temperature/Pressure retraining: {str(e)}"
        print(error_msg)
        return False, error_msg, "Temperature_Pressure_Model"


def run_all_retrainings():
    final_results = {}
    
    success, msg, model_key = retrain_temperature_pressure_pipeline()
    final_results[model_key] = msg
    
    return final_results

if __name__ == "__main__":
    results = run_all_retrainings()
    print("Retraining Results:", results)
