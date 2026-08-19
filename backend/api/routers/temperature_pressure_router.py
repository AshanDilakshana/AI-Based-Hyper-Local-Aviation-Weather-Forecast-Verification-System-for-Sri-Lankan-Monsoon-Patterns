from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import pandas as pd
import joblib
import os
from sqlalchemy.orm import Session
from datetime import datetime

# Adjust paths assuming this file is in backend/api/routers/
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
MODEL_DIR = os.path.join(BASE_DIR, "Models", "Temperature")

import sys
sys.path.append(BASE_DIR)

from preprocessing_and_feature_engineering.temperature_pressure_model.unified_pipeline import UnifiedWeatherPipeline
from backend.data.database import get_db
from backend.data.models import PredictionRecord

router = APIRouter(prefix="/predict", tags=["Temperature & Pressure Forecast"])

from backend.api.schemas import TempPressPredictionRequest

# Global model instance
model = None
pipeline = None

def load_Temp_Press_models():
    """Loads the Temperature & Pressure models into memory."""
    global model, pipeline
    try:
        model = joblib.load(os.path.join(MODEL_DIR, "weather_model.pkl"))
        pipeline = UnifiedWeatherPipeline(model_dir=MODEL_DIR)
        print("Temperature & Pressure model loaded successfully.")
    except Exception as e:
        print(f"Warning: Temperature & Pressure model could not be loaded: {e}")

# Call immediately on module load
load_Temp_Press_models()


@router.post("/temp-press")
def predict_temperature_pressure(request: TempPressPredictionRequest, db: Session = Depends(get_db)):
    if model is None or pipeline is None:
        raise HTTPException(status_code=500, detail="Temperature/Pressure model is not loaded.")
        
    try:
        # Convert request to single-row dataframe
        df = pd.DataFrame([request.dict()])
        
        # Preprocess using the unified pipeline
        X_scaled = pipeline.process_inference_data(df)
        
        # Predict using MultiOutputRegressor
        predictions = model.predict(X_scaled)
        
        predicted_temp = float(predictions[0][0])
        predicted_press = float(predictions[0][1])
        
        # Optional: Log to DB (mimicking the team's pattern)
        record = PredictionRecord(
            timestamp_utc=datetime.utcnow(),
            predicted_temperature=predicted_temp,
            predicted_pressure=predicted_press,
            model_version="temp_press_v1"
        )
        db.add(record)
        db.commit()
        
        return {
            "prediction": {
                "temperature_C": round(predicted_temp, 2),
                "pressure_hPa": round(predicted_press, 2)
            }
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
