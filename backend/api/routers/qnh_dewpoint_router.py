from fastapi import APIRouter, HTTPException
import joblib
import pandas as pd
import os
import math

router = APIRouter(
    prefix="/qnh-dewpoint",
    tags=["QNH, Dewpoint & RH Forecasting Models"]
)

# Global variables to hold loaded models
qnh_3h_model = None
dewpoint_3h_model = None

def load_QNH_Dewpoint_models():
    """
    Loads or reloads the LightGBM models into memory.
    Called on startup and after automated retraining.
    """
    global qnh_3h_model, dewpoint_3h_model
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    
    # Paths (Aligned with the new training script paths)
    qnh_primary = os.path.join(base_dir, 'Models', 'qnh_models', 'qnh_3h_lgbm.pkl')
    qnh_backup = os.path.join(base_dir, 'Models', 'qnh_models', 'qnh_3h_lgbm_backup.pkl')
    
    dewpoint_primary = os.path.join(base_dir, 'Models', 'dewpoint_models', 'dewpoint_3h_lgbm.pkl')
    dewpoint_backup = os.path.join(base_dir, 'Models', 'dewpoint_models', 'dewpoint_3h_lgbm_backup.pkl')
    
    # Load QNH Model
    try:
        if os.path.exists(qnh_primary):
            qnh_3h_model = joblib.load(qnh_primary)
            print("Loaded Primary QNH 3H Model.")
        else:
            raise FileNotFoundError(f"Primary QNH model not found at {qnh_primary}")
    except Exception as e:
        print(f"Failed to load primary QNH model: {e}. Attempting backup...")
        try:
            if os.path.exists(qnh_backup):
                qnh_3h_model = joblib.load(qnh_backup)
                print("Loaded Backup QNH 3H Model.")
            else:
                print("No Backup QNH model found.")
        except Exception as backup_e:
            print(f"Failed to load backup QNH model: {backup_e}")
            
    # Load Dewpoint Model
    try:
        if os.path.exists(dewpoint_primary):
            dewpoint_3h_model = joblib.load(dewpoint_primary)
            print("Loaded Primary Dewpoint 3H Model.")
        else:
            raise FileNotFoundError(f"Primary Dewpoint model not found at {dewpoint_primary}")
    except Exception as e:
        print(f"Failed to load primary Dewpoint model: {e}. Attempting backup...")
        try:
            if os.path.exists(dewpoint_backup):
                dewpoint_3h_model = joblib.load(dewpoint_backup)
                print("Loaded Backup Dewpoint 3H Model.")
            else:
                print("No Backup Dewpoint model found.")
        except Exception as backup_e:
            print(f"Failed to load backup Dewpoint model: {backup_e}")

# Load models initially when router is imported
load_QNH_Dewpoint_models()

@router.post("/predict/3h")
def predict_qnh_dewpoint_3h():
    """
    Predict QNH and Dewpoint 3 hours into the future using the latest data
    from the live database, and derive RH using the Magnus formula.
    """
    if not qnh_3h_model or not dewpoint_3h_model:
        raise HTTPException(status_code=503, detail="Models not loaded or unavailable.")
        
    try:
        # Determine paths
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        db_path = os.path.join(base_dir, 'weather_data.db')
        
        # We need to import the pipelines dynamically to avoid circular imports 
        # or path issues during startup
        import sys
        if base_dir not in sys.path:
            sys.path.append(base_dir)
            
        from preprocessing_and_feature_engineering.qnh_prediction_model.unified_pipeline import QNHUnifiedPipeline
        from preprocessing_and_feature_engineering.dewpoint_prediction_model.unified_pipeline import DewpointUnifiedPipeline
        
        from backend.data.database import engine
        
        # Run QNH Pipeline for inference (is_training=False prevents target NaN dropping)
        qnh_pipeline = QNHUnifiedPipeline(db_path, engine=engine)
        df_qnh_all = qnh_pipeline.run_pipeline(is_training=False)
        
        if df_qnh_all.empty:
            raise ValueError("QNH Pipeline returned empty dataset. Not enough live data.")
            
        # Get the latest row
        latest_qnh_row = df_qnh_all.iloc[[-1]]
        qnh_features = qnh_pipeline.get_feature_columns(latest_qnh_row)
        input_qnh_df = latest_qnh_row[qnh_features]
        
        # Run Dewpoint Pipeline for inference
        dew_pipeline = DewpointUnifiedPipeline(db_path, engine=engine)
        df_dew_all = dew_pipeline.run_pipeline(is_training=False)
        
        if df_dew_all.empty:
            raise ValueError("Dewpoint Pipeline returned empty dataset. Not enough live data.")
            
        latest_dew_row = df_dew_all.iloc[[-1]]
        dew_features = dew_pipeline.get_feature_columns(latest_dew_row)
        input_dew_df = latest_dew_row[dew_features]
        
        # Predictions
        pred_qnh = qnh_3h_model.predict(input_qnh_df)[0]
        pred_dewpoint = dewpoint_3h_model.predict(input_dew_df)[0]
        
        # =================================================
        # SAVE TO UNIFIED FORECAST TABLE & CALCULATE RH
        # =================================================
        from backend.data.database import SessionLocal
        from backend.data.models import ModelsForecast
        from datetime import datetime, timedelta
        
        db = SessionLocal()
        try:
            from backend.data.models import WeatherData
            latest_ob = db.query(WeatherData).order_by(WeatherData.timestamp_utc.desc()).first()
            if latest_ob and latest_ob.timestamp_utc:
                target_time = (latest_ob.timestamp_utc + timedelta(hours=3)).replace(minute=0, second=0, microsecond=0)
            else:
                target_time = (datetime.utcnow() + timedelta(hours=3)).replace(minute=0, second=0, microsecond=0)
                
            unified_record = db.query(ModelsForecast).filter(ModelsForecast.target_time_utc == target_time).first()
            
            # Use predicted temperature if available, otherwise fallback to current
            if unified_record and unified_record.temperature_c is not None:
                calc_temp = unified_record.temperature_c
            else:
                calc_temp = latest_dew_row['dry_temp_c'].values[0] if 'dry_temp_c' in latest_dew_row else pred_dewpoint + 5
                
            # August-Roche-Magnus formula for derived RH
            a = 17.67
            b = 243.5
            rh = 100 * math.exp((a * pred_dewpoint) / (b + pred_dewpoint) - (a * calc_temp) / (b + calc_temp))
            rh = round(min(100, max(0, rh)), 2)
        
            if not unified_record:
                unified_record = ModelsForecast(target_time_utc=target_time)
                db.add(unified_record)
                
            unified_record.qnh_hpa = float(pred_qnh)
            unified_record.dew_point_c = float(pred_dewpoint)
            unified_record.rh_percent = float(rh)
            db.add(unified_record)
            db.commit()
        except Exception as db_e:
            print(f"[ERROR] Failed to save to ModelsForecast: {db_e}")
        finally:
            db.close()
        
        return {
            "timestamp_utc": str(latest_qnh_row['timestamp_utc'].values[0]),
            "predicted_qnh_3h": round(pred_qnh, 2),
            "predicted_dewpoint_3h": round(pred_dewpoint, 2),
            "derived_rh_3h": rh,
            "status": "SUCCESS"
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))
