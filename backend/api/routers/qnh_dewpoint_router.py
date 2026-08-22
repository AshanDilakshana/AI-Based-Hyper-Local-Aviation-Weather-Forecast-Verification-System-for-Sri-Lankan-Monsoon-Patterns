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
def predict_qnh_dewpoint_3h(features: dict):
    """
    Predict QNH and Dewpoint 3 hours into the future, 
    and derive RH using the Magnus formula.
    """
    global qnh_3h_model, dewpoint_3h_model
    
    if not qnh_3h_model or not dewpoint_3h_model:
        raise HTTPException(status_code=503, detail="Models not loaded or unavailable.")
        
    try:
        # Expected features dictate what the pipeline generated. 
        # In a real API, we would run the pipeline over the inputs.
        # For simplicity, assuming the features dict matches model expectations exactly.
        input_df = pd.DataFrame([features])
        
        pred_qnh = qnh_3h_model.predict(input_df)[0]
        pred_dewpoint = dewpoint_3h_model.predict(input_df)[0]
        
        # Determine RH using predicted dewpoint and assumed stable or predicted temp
        # For this demonstration, we assume dry_temp is passed in features
        temp = features.get('dry_temp_c', pred_dewpoint + 5) # Fallback if not provided
        
        # August-Roche-Magnus formula
        a = 17.67
        b = 243.5
        rh = 100 * math.exp((a * pred_dewpoint) / (b + pred_dewpoint) - (a * temp) / (b + temp))
        rh = round(min(100, max(0, rh)), 2)
        
        return {
            "predicted_qnh_3h": round(pred_qnh, 2),
            "predicted_dewpoint_3h": round(pred_dewpoint, 2),
            "derived_rh_3h": rh,
            "status": "SUCCESS"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
