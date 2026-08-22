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
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        
        qnh_model_path = os.path.join(base_dir, 'Models', 'qnh_models', '3h prediction model', 'qnh_3h_lightgbm.pkl')
        dewpoint_model_path = os.path.join(base_dir, 'Models', 'dewpoint_models', '3h prediction model', 'dewpoint_3h_lightgbm.pkl')
        
        if os.path.exists(qnh_model_path):
            qnh_3h_model = joblib.load(qnh_model_path)
            print("Loaded QNH 3H Model.")
            
        if os.path.exists(dewpoint_model_path):
            dewpoint_3h_model = joblib.load(dewpoint_model_path)
            print("Loaded Dewpoint 3H Model.")
            
    except Exception as e:
        print(f"Error loading QNH/Dewpoint models: {e}")

# Load models initially when router is imported
load_QNH_Dewpoint_models()

@router.post("/predict/3h")
def predict_qnh_dewpoint_3h():
    """
    Predict QNH and Dewpoint 3 hours into the future using the latest data
    from the live database, and derive RH using the Magnus formula.
    """
    global qnh_3h_model, dewpoint_3h_model
    
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
        
        # Run QNH Pipeline for inference (is_training=False prevents target NaN dropping)
        qnh_pipeline = QNHUnifiedPipeline(db_path)
        df_qnh_all = qnh_pipeline.run_pipeline(is_training=False)
        
        if df_qnh_all.empty:
            raise ValueError("QNH Pipeline returned empty dataset. Not enough live data.")
            
        # Get the latest row
        latest_qnh_row = df_qnh_all.iloc[[-1]]
        qnh_features = qnh_pipeline.get_feature_columns(latest_qnh_row)
        input_qnh_df = latest_qnh_row[qnh_features]
        
        # Run Dewpoint Pipeline for inference
        dew_pipeline = DewpointUnifiedPipeline(db_path)
        df_dew_all = dew_pipeline.run_pipeline(is_training=False)
        
        if df_dew_all.empty:
            raise ValueError("Dewpoint Pipeline returned empty dataset. Not enough live data.")
            
        latest_dew_row = df_dew_all.iloc[[-1]]
        dew_features = dew_pipeline.get_feature_columns(latest_dew_row)
        input_dew_df = latest_dew_row[dew_features]
        
        # Predictions
        pred_qnh = qnh_3h_model.predict(input_qnh_df)[0]
        pred_dewpoint = dewpoint_3h_model.predict(input_dew_df)[0]
        
        # Retrieve current temperature from the latest dewpoint row (it has dry_temp_c)
        current_temp = latest_dew_row['dry_temp_c'].values[0] if 'dry_temp_c' in latest_dew_row else pred_dewpoint + 5
        
        # August-Roche-Magnus formula for derived RH
        a = 17.67
        b = 243.5
        rh = 100 * math.exp((a * pred_dewpoint) / (b + pred_dewpoint) - (a * current_temp) / (b + current_temp))
        rh = round(min(100, max(0, rh)), 2)
        
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
