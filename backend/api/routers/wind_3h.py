from fastapi import APIRouter, HTTPException
import xgboost as xgb
import pandas as pd
import numpy as np
import os
from backend.api.schemas import WindPredictionRequest, WindPredictionResponse

router = APIRouter(
    prefix="/wind_3h",
    tags=["3-Hour Wind Forecast Model"]
)

# Load the AI Model globally for this router
MODEL_PATH = os.path.join(os.path.dirname(__file__), '../../../3h prediction model/xgboost_wind_model_3h.json')
try:
    model_3h = xgb.XGBRegressor()
    model_3h.load_model(MODEL_PATH)
except Exception as e:
    print(f"Warning: Could not load 3H wind model. Error: {e}")
    model_3h = None

def calculate_aviation_winds(wind_speed: float, wind_dir: float, runway_heading: int):
    """Calculates Headwind and Crosswind for a specific runway."""
    angle_diff = np.radians(wind_dir - runway_heading)
    crosswind = wind_speed * np.sin(angle_diff)
    headwind = wind_speed * np.cos(angle_diff)
    return abs(crosswind), headwind

@router.post("/predict", response_model=WindPredictionResponse)
def predict_wind_3h(request: WindPredictionRequest):
    """
    Endpoint to predict wind speed 3 hours into the future.
    """
    if model_3h is None:
        raise HTTPException(status_code=500, detail="3H Wind AI Model is not loaded on the server.")

    # Time parsing
    hour = int(request.time_utc[:2]) if request.time_utc and len(request.time_utc) >= 2 else 0

    features = pd.DataFrame([{
        'Wind Dir_Sin': np.sin(np.radians(request.wind_dir)),
        'Wind Dir_Cos': np.cos(np.radians(request.wind_dir)),
        'Hour_Sin': np.sin(2 * np.pi * hour / 24.0),
        'Hour_Cos': np.cos(2 * np.pi * hour / 24.0),
        'Wind speed(Kts)_lag_3h': request.past_wind_speed,
        'Dew_Point_Depression': request.temperature - request.dew_point,
        'Dry Temp(0C)': request.temperature,
        'RH(%)': request.humidity,
        'QNH(hPa)': request.qnh_hpa
    }])

    predicted_wind_speed = float(model_3h.predict(features)[0])

    crosswind, headwind = calculate_aviation_winds(
        predicted_wind_speed, 
        request.wind_dir, 
        request.runway_heading
    )

    status = "SAFE"
    message = "Forecast for 3 hours ahead: Crosswind components are within normal limits."
    if crosswind > 15:
        status = "WARNING"
        message = "Forecast for 3 hours ahead: High crosswind likely! Plan contingencies."
    if crosswind > 25:
        status = "DANGER"
        message = "Forecast for 3 hours ahead: Severe crosswind. Exceeds standard operating limits."

    return WindPredictionResponse(
        predicted_wind_speed_kts=round(predicted_wind_speed, 2),
        headwind_kts=round(headwind, 2),
        crosswind_kts=round(crosswind, 2),
        runway=f"RWY {str(request.runway_heading).zfill(3)}",
        status=status,
        message=message
    )
