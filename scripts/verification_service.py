import os
import sys
from datetime import datetime, timedelta
import numpy as np

# Ensure backend modules can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from backend.data.database import SessionLocal
from backend.data.models import WeatherData, ModelsForecast
from backend.api.routers.temperature_pressure_router import (
    prepare_features_with_lags,
    prepare_lstm_sequence,
    temp_model,
    temp_scaler,
    temp_features,
    press_model,
    press_scaler,
    press_features,
    lstm_model,
    hybrid_model,
    lstm_scaler_X,
    lstm_scaler_y,
    load_Temp_Press_models
)


def run_auto_prediction_and_save():
    """
    Generates an automated 3H temperature and pressure prediction using the latest
    observation in weather_data and saves it to temp_pressure_prediction_records.
    """
    # Ensure models are loaded
    if temp_model is None or press_model is None:
        load_Temp_Press_models()
        
    db = SessionLocal()
    try:
        # Check if latest record exists
        latest_ob = db.query(WeatherData).order_by(WeatherData.timestamp_utc.desc()).first()
        if not latest_ob:
            print("No observations available in weather_data for auto prediction.")
            return None

        # Build features and predict
        df = prepare_features_with_lags(db)
        
        X_temp = df.reindex(columns=temp_features, fill_value=0)
        X_temp_scaled = temp_scaler.transform(X_temp)
        predicted_temp = float(temp_model.predict(X_temp_scaled)[0])
        
        X_press = df.reindex(columns=press_features, fill_value=0)
        X_press_scaled = press_scaler.transform(X_press)
        predicted_press_diff = float(press_model.predict(X_press_scaled)[0])
        
        current_pressure = float(df['qnh_hpa'].iloc[0])
        predicted_press = current_pressure + predicted_press_diff
        
        # Hybrid LSTM enhancement if available
        try:
            seq = prepare_lstm_sequence(db)
            seq_scaled = lstm_scaler_X.transform(seq)
            seq_scaled = np.expand_dims(seq_scaled, axis=0)
            
            lstm_pred_scaled = lstm_model.predict(seq_scaled, verbose=0)
            lstm_pred = lstm_scaler_y.inverse_transform(lstm_pred_scaled)[0]
            
            curr_temp = seq[-1][0]
            curr_press = seq[-1][1]
            hybrid_features = np.array([[curr_temp, curr_press, lstm_pred[0], lstm_pred[1]]])
            
            final_pred = hybrid_model.predict(hybrid_features)[0]
            predicted_temp = float(final_pred[0])
            predicted_press = float(final_pred[1])
        except Exception as e:
            pass

        target_time = (datetime.utcnow() + timedelta(hours=3)).replace(minute=0, second=0, microsecond=0)
        
        unified_record = db.query(ModelsForecast).filter(ModelsForecast.target_time_utc == target_time).first()
        if not unified_record:
            unified_record = ModelsForecast(target_time_utc=target_time)
            db.add(unified_record)
            
        unified_record.temperature_c = round(predicted_temp, 2)
        unified_record.pressure_hpa = round(predicted_press, 2)
        
        db.commit()
        print(f"[{datetime.now()}] Automated forecast saved: Temp={unified_record.temperature_c}C, Press={unified_record.pressure_hpa}hPa (Target: {unified_record.target_time_utc} UTC)")
        return True
    except Exception as e:
        print(f"[{datetime.now()}] Error during auto prediction: {e}")
        db.rollback()
        return None
    finally:
        db.close()
