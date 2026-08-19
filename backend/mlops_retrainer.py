import os
import sys
import pandas as pd
from datetime import datetime
import importlib.util
import glob

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



def load_and_run_plugins(db_session=None):
    """
    Dynamically loads and runs all retraining plugins from backend/mlops_plugins/
    """
    results = {}
    base_dir = os.path.dirname(os.path.abspath(__file__))
    plugins_dir = os.path.join(base_dir, 'mlops_plugins')
    
    if not os.path.exists(plugins_dir):
        return results
        
    plugin_files = glob.glob(os.path.join(plugins_dir, "*.py"))
    
    for file_path in plugin_files:
        if os.path.basename(file_path) == "__init__.py":
            continue
            
        module_name = os.path.basename(file_path)[:-3]
        
        try:
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            if hasattr(module, 'retrain'):
                success, msg, model_key = module.retrain()
                results[model_key] = msg
        except Exception as e:
            print(f"Failed to load/run plugin {module_name}: {e}")
            results[module_name] = f"Plugin Error: {e}"
            
    return results

def run_all_retrainings():
    # ---------------------------------------------------------
    # => NOW USING DYNAMIC PLUGIN ARCHITECTURE!
    # ---------------------------------------------------------
    
    plugin_results = load_and_run_plugins()
    
    final_results = {}
    
    final_results.update(plugin_results)
    
    return final_results

if __name__ == "__main__":
    results = run_all_retrainings()
    print("Retraining Results:", results)
