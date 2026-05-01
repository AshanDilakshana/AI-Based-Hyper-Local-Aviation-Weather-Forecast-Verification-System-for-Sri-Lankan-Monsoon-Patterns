from fastapi import APIRouter, HTTPException
import xgboost as xgb
import pandas as pd
import numpy as np
import os
from backend.api.schemas import WindPredictionRequest, WindPredictionResponse

# Create an APIRouter specifically for your Wind Model
router = APIRouter(
    prefix="/wind",
    tags=["Wind Prediction Model (Ashan's Part)"]
)

# Load the AI Model globally for this router
MODEL_PATH = os.path.join(os.path.dirname(__file__), '../../../wind prediction model/xgboost_wind_model.json')
try:
    model = xgb.XGBRegressor()
    model.load_model(MODEL_PATH)
except Exception as e:
    print(f"Warning: Could not load wind model. Error: {e}")
    model = None

def calculate_aviation_winds(wind_speed: float, wind_dir: float, runway_heading: int):
    """Calculates Headwind and Crosswind for a specific runway."""
    angle_diff = np.radians(wind_dir - runway_heading)
    crosswind = wind_speed * np.sin(angle_diff)
    headwind = wind_speed * np.cos(angle_diff)
    return abs(crosswind), headwind

@router.post("/predict", response_model=WindPredictionResponse)

def predict_wind(request: WindPredictionRequest):
    """
    Endpoint to predict next hour's wind speed and calculate crosswind.
    """
    if model is None:
        raise HTTPException(status_code=500, detail="Wind AI Model is not loaded on the server.")

    # 1. Manually build the exact 6 features the XGBoost model expects
    features = pd.DataFrame([{
        'Wind Dir_Sin': np.sin(np.radians(request.wind_dir)),
        'Wind Dir_Cos': np.cos(np.radians(request.wind_dir)),
        'Wind speed(Kts)_lag_3h': request.past_wind_speed,
        'Dew_Point_Depression': request.temperature - request.dew_point,
        'Dry Temp(0C)': request.temperature,
        'RH(%)': request.humidity
    }])

    # 2. Get the Prediction
    predicted_wind_speed = float(model.predict(features)[0])

    # 3. Aviation Calculations
    crosswind, headwind = calculate_aviation_winds(
        predicted_wind_speed, 
        request.wind_dir, 
        request.runway_heading
    )

    # 4. Determine Alert Status
    status = "SAFE"
    message = "Crosswind components are within normal operating limits."
    if crosswind > 15:
        status = "WARNING"
        message = "High crosswind detected! Exercise caution during landing."
    if crosswind > 25:
        status = "DANGER"
        message = "Severe crosswind. Exceeds standard operating limits for most commercial aircraft."

    return WindPredictionResponse(
        predicted_wind_speed_kts=round(predicted_wind_speed, 2),
        headwind_kts=round(headwind, 2),
        crosswind_kts=round(crosswind, 2),
        runway=f"RWY {str(request.runway_heading).zfill(3)}",
        status=status,
        message=message
    )

@router.post("/ingest")
def ingest_data():
    return {"message": "Data ingestion endpoint placeholder for Wind data."}

@router.post("/retrain")
def retrain_model():
    return {"message": "Retraining pipeline endpoint placeholder for Wind model."}
