import os
import sys
from datetime import datetime, timedelta
import numpy as np

# Ensure backend modules can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from backend.data.database import SessionLocal
from backend.data.models import WeatherData, TempPressurePredictionRecord
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

def verify_past_temp_pressure_predictions():
    """
    Checks all unverified prediction records in temp_pressure_prediction_records,
    finds the corresponding actual observation in weather_data for the target time,
    calculates temperature and pressure errors, and updates the record.
    """
    db = SessionLocal()
    verified_count = 0
    try:
        unverified_records = db.query(TempPressurePredictionRecord).filter(
            TempPressurePredictionRecord.is_verified == 0
        ).all()

        for rec in unverified_records:
            # Find the actual observation matching target date and HOUR (since minutes won't match exactly)
            target_hour = rec.target_time_utc[:2] if rec.target_time_utc else "00"
            actual = db.query(WeatherData).filter(
                WeatherData.year == rec.target_year,
                WeatherData.month == rec.target_month,
                WeatherData.date == rec.target_date,
                WeatherData.time_utc.like(f"{target_hour}%")
            ).first()

            if actual and actual.dry_temp_c is not None and actual.qnh_hpa is not None:
                rec.actual_temperature_c = float(actual.dry_temp_c)
                rec.actual_pressure_hpa = float(actual.qnh_hpa)
                if rec.predicted_temperature_c is not None:
                    rec.temperature_error = round(abs(rec.predicted_temperature_c - actual.dry_temp_c), 2)
                if rec.predicted_pressure_hpa is not None:
                    rec.pressure_error = round(abs(rec.predicted_pressure_hpa - actual.qnh_hpa), 2)
                rec.is_verified = 1
                verified_count += 1

        db.commit()
        if verified_count > 0:
            print(f"[{datetime.now()}] SUCCESS: Verified {verified_count} past prediction records.")
    except Exception as e:
        print(f"[{datetime.now()}] Error during prediction verification: {e}")
        db.rollback()
    finally:
        db.close()
    return verified_count

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

        target_time = datetime.utcnow() + timedelta(hours=3)
        created_at_utc = datetime.utcnow()

        # Thermodynamic Hazard Precursor Logic
        current_temp = float(df['dry_temp_c'].iloc[0])
        temp_roc_per_hr = (predicted_temp - current_temp) / 3.0
        
        # VCBI 75th percentile pressure is ~1012.4, so 1012.0 is a solid "High" threshold.
        # A drop of 1.0C over 3 hours (-0.33/hr) is significant given std dev of 1.87.
        is_rapid_cooling = temp_roc_per_hr <= -0.33
        is_high_stable_pressure = predicted_press >= 1012.0 and abs(predicted_press - current_pressure) <= 0.5
        
        status_val = "HAZARD: RADIATION FOG" if (is_rapid_cooling and is_high_stable_pressure) else "SAFE"

        new_record = TempPressurePredictionRecord(
            created_at=created_at_utc,
            forecast_type="3H_AUTO",
            target_year=target_time.year,
            target_month=target_time.month,
            target_date=target_time.day,
            target_time_utc=target_time.strftime("%H%M"),
            predicted_temperature_c=round(predicted_temp, 2),
            predicted_pressure_hpa=round(predicted_press, 2),
            status=status_val,
            is_verified=0
        )
        db.add(new_record)
        db.commit()
        db.refresh(new_record)
        print(f"[{datetime.now()}] Automated forecast saved: Temp={new_record.predicted_temperature_c}C, Press={new_record.predicted_pressure_hpa}hPa (Target: {new_record.target_time_utc} UTC)")
        return new_record
    except Exception as e:
        print(f"[{datetime.now()}] Error during auto prediction: {e}")
        db.rollback()
        return None
    finally:
        db.close()
