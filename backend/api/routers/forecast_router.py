from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from pydantic import BaseModel
from typing import Optional

from backend.data.database import get_db
from backend.data.models import SystemLogs

router = APIRouter(
    prefix="/forecasts",
    tags=["forecasts"],
)



from backend.api.schemas import WindPredictionRequest
from backend.data.models import WeatherData

@router.get("/ai-predict-all")
def get_all_ai_predictions(db: Session = Depends(get_db)):
    """
    Get predictions from all AI models (Wind, Temp, Cloud, QNH, etc.) in a single call.
    """
    
    # Fetch the latest record from DB to construct the request payload
    latest_weather = db.query(WeatherData).order_by(WeatherData.id.desc()).first()
    if not latest_weather:
        raise HTTPException(status_code=404, detail="No historical weather data found to make predictions.")
        
    wind_req = WindPredictionRequest(
        temperature=latest_weather.dry_temp_c,
        dew_point=latest_weather.dew_point_c,
        humidity=latest_weather.rh_percent,
        wind_dir=latest_weather.wind_dir,
        runway_heading=40, # Default BIA runway 04
        time_utc=str(latest_weather.time_utc).zfill(4) if latest_weather.time_utc else "0000",
        qnh_hpa=latest_weather.qnh_hpa
    )

    # 1. Wind Hybrid Model Prediction (Ashan)
    try:
        from backend.api.routers.wind_router import predict_wind_hybrid_3h
        wind_prediction = predict_wind_hybrid_3h(wind_req)
    except Exception as e:
        wind_prediction = {"error": f"Wind model failed: {str(e)}"}

    # ---------------------------------------------------------
    # (imash) Temperature & Pressure Model Integration
    # ---------------------------------------------------------
    try:
        from backend.api.schemas import TempPressPredictionRequest
        from backend.api.routers.temperature_pressure_router import predict_temperature_pressure
        
        temp_req = TempPressPredictionRequest(
            temperature=latest_weather.dry_temp_c,
            humidity=latest_weather.rh_percent,
            pressure=latest_weather.qnh_hpa,
            dew_point=latest_weather.dew_point_c,
            wind_speed=latest_weather.wind_speed_kts,
            wind_direction=latest_weather.wind_dir,
            visibility=latest_weather.visibility
        )
        temp_prediction = predict_temperature_pressure(temp_req, db)
    except Exception as e:
        temp_prediction = {"error": f"Temp/Pressure model failed: {str(e)}"}

    # ---------------------------------------------------------
    # (sachiii) Cloud & Visibility Model Integration
    # ---------------------------------------------------------
    try:
        from backend.api.schemas import CloudVisibilityRequest
        from backend.api.routers.cloud_visibility_router import predict_cloud_visibility
        
        hour_val = float(str(latest_weather.time_utc)[:2]) if latest_weather.time_utc and len(str(latest_weather.time_utc)) >= 2 else 12.0
        
        cloud_req = CloudVisibilityRequest(
            temp=latest_weather.dry_temp_c,
            dew=latest_weather.dew_point_c,
            rh=latest_weather.rh_percent,
            qnh=latest_weather.qnh_hpa,
            wind=latest_weather.wind_speed_kts,
            month=latest_weather.month,
            hour=hour_val,
            wind_dir=latest_weather.wind_dir,
            weather_encoded=0.0
        )
        cloud_visibility_prediction = predict_cloud_visibility(cloud_req)
    except Exception as e:
        cloud_visibility_prediction = {"error": f"Cloud model failed: {str(e)}"}

    # ---------------------------------------------------------
    # (viji) QNH & Dewpoint Model Integration
    # ---------------------------------------------------------
    try:
        from backend.api.routers.qnh_dewpoint_router import predict_qnh_dewpoint_3h
        qnh_dewpoint_prediction = predict_qnh_dewpoint_3h()
    except Exception as e:
        qnh_dewpoint_prediction = {"error": f"QNH/Dewpoint model failed: {str(e)}"}


    return {
        "timestamp_utc": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "wind_forecast": wind_prediction,
        "temperature_pressure_forecast": temp_prediction,
        "cloud_visibility_forecast": cloud_visibility_prediction,
        "qnh_dewpoint_forecast": qnh_dewpoint_prediction,
    }

