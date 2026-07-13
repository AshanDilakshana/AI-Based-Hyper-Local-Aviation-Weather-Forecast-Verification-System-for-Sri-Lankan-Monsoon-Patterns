import os
import sys
import pandas as pd
import joblib
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from backend.data.database import SessionLocal
from backend.data.models import WeatherData, SystemLogs
from Models.weather_pipeline import UnifiedWeatherPipeline
from Models.weather_trainer import train_for_mlops, evaluate_old_model

def get_all_historical_data(db_session):
    records = db_session.query(WeatherData).order_by(WeatherData.id.asc()).all()
    data = []
    for r in records:
        data.append({
            'Year': r.year,
            'Month': r.month,
            'Date': r.date,
            'Time(UTC)': str(r.time_utc).zfill(4) if r.time_utc else "0000",
            'Wind Dir.': r.wind_dir,
            'Wind speed(Kts)': r.wind_speed_kts,
            'Dry tem(0C)': r.dry_temp_c,
            'Dew point(0C)': r.dew_point_c,
            'RH(%)': r.rh_percent,
            'QNH (hPa)': r.qnh_hpa,
            'Visibility': r.visibility,
            'Clouds': r.clouds if r.clouds else 'FEW',
            'Weather': r.weather if r.weather else 'NSW'
        })
    return pd.DataFrame(data)

def log_event(db_session, level, component, message, details=None):
    log = SystemLogs(level=level, component=component, message=message, details=details)
    db_session.add(log)
    db_session.commit()
    print(f"[{level}] {component}: {message}")

def retrain_model_pipeline():
    db = SessionLocal()
    component = "MLOps_3H_Weather"
    targets = ["target_temperature", "target_pressure", "target_humidity"]
    
    try:
        log_event(db, "INFO", component, "Started Retraining Process")
        
        df_raw = get_all_historical_data(db)
        if len(df_raw) < 100:
            log_event(db, "WARNING", component, "Not enough database weather data to retrain (<100 rows).")
            return False, "Not enough data"
            
        pipeline = UnifiedWeatherPipeline()
        X, y = pipeline.process_training_data(df_raw)
        
        df_processed = X.copy()
        for t in targets:
            df_processed[t] = y[t]
            
        if df_processed.empty:
            log_event(db, "ERROR", component, "Processed data is empty.")
            return False, "Processing failed"
            
        log_event(db, "INFO", component, "Training New Model...")
        new_model, new_mae, X_test, y_test = train_for_mlops(df_processed, targets)
        
        model_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../Models/3h prediction model'))
        model_path = os.path.join(model_dir, 'weather_model.pkl')
        scaler_path = os.path.join(model_dir, 'scaler.pkl')
        features_path = os.path.join(model_dir, 'feature_columns.pkl')
        
        old_mae = evaluate_old_model(model_path, X_test, y_test)
        
        if old_mae is None:
            log_event(db, "INFO", component, f"No existing model found. Saving new model. MAE: {new_mae:.4f}")
            os.makedirs(model_dir, exist_ok=True)
            joblib.dump(new_model, model_path)
            
            # Save corresponding scaler and features
            from sklearn.preprocessing import StandardScaler
            scaler = StandardScaler()
            scaler.fit(X)
            joblib.dump(scaler, scaler_path)
            joblib.dump(list(X.columns), features_path)
            
            log_event(db, "SUCCESS", component, "New model deployed successfully.")
            return True, "Model Deployed"
            
        details = f"{{\"old_mae\": {old_mae:.4f}, \"new_mae\": {new_mae:.4f}}}"
        
        if new_mae < old_mae:
            log_event(db, "SUCCESS", component, f"New Model is better! (Old MAE: {old_mae:.4f}, New MAE: {new_mae:.4f})", details)
            
            backup_path = model_path.replace('.pkl', '_backup.pkl')
            if os.path.exists(backup_path):
                os.remove(backup_path)
            if os.path.exists(model_path):
                os.rename(model_path, backup_path)
                
            joblib.dump(new_model, model_path)
            from sklearn.preprocessing import StandardScaler
            scaler = StandardScaler()
            scaler.fit(X)
            joblib.dump(scaler, scaler_path)
            joblib.dump(list(X.columns), features_path)
            
            log_event(db, "INFO", component, "Versioning complete. Old model is now backup.")
            ret = True, "Model Promoted"
        else:
            log_event(db, "WARNING", component, f"New Model is worse or equal. Rejected. (Old MAE: {old_mae:.4f}, New MAE: {new_mae:.4f})", details)
            ret = False, "Model Rejected"

    except Exception as e:
        log_event(db, "ERROR", component, f"Error during retraining: {str(e)}")
        ret = False, str(e)
    finally:
        db.close()
        
    return ret

def run_all_retrainings():
    res, msg = retrain_model_pipeline()
    return {
        "3H_Weather_Model": msg
    }

if __name__ == "__main__":
    results = run_all_retrainings()
    print("Retraining Results:", results)
