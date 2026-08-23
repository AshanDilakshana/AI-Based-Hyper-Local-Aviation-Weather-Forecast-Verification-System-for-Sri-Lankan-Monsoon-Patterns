from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from pydantic import BaseModel
from typing import Optional

from backend.data.database import get_db
from backend.data.models import VerifiedForecast, SystemLogs

router = APIRouter(
    prefix="/forecasts",
    tags=["forecasts"],
)

class VerifiedForecastCreate(BaseModel):
    target_time: datetime
    created_at: Optional[datetime] = None
    dry_temp_c: Optional[float] = None
    wind_speed_kts: Optional[float] = None
    wind_dir: Optional[float] = None
    rh_percent: Optional[float] = None
    clouds: Optional[str] = None
    visibility: Optional[float] = None
    qnh_hpa: Optional[float] = None
    headwind_kts: Optional[float] = None
    crosswind_kts: Optional[float] = None

@router.post("/verify")
def verify_forecast(forecast: VerifiedForecastCreate, db: Session = Depends(get_db)):
    try:
        new_record = VerifiedForecast(
            target_time=forecast.target_time,
            created_at=forecast.created_at or datetime.utcnow(),
            dry_temp_c=forecast.dry_temp_c,
            wind_speed_kts=forecast.wind_speed_kts,
            wind_dir=forecast.wind_dir,
            rh_percent=forecast.rh_percent,
            clouds=forecast.clouds,
            visibility=forecast.visibility,
            qnh_hpa=forecast.qnh_hpa,
            headwind_kts=forecast.headwind_kts,
            crosswind_kts=forecast.crosswind_kts
        )
        db.add(new_record)
        
        # Log to SystemLogs
        audit_log = SystemLogs(
            timestamp_utc=datetime.utcnow(),
            level="SUCCESS",
            component="Forecast_Verification",
            message="Forecaster verified and published 3H forecast guidance.",
            details=f"Wind: {forecast.wind_speed_kts}kts / {forecast.wind_dir}°, Temp: {forecast.dry_temp_c}°C"
        )
        db.add(audit_log)
        
        db.commit()
        db.refresh(new_record)
        return {"message": "Verified forecast saved successfully", "id": new_record.id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to save verified forecast: {str(e)}")

@router.get("/verified/latest")
def get_latest_verified_forecast(db: Session = Depends(get_db)):
    record = db.query(VerifiedForecast).order_by(VerifiedForecast.created_at.desc()).first()
    if not record:
        raise HTTPException(status_code=404, detail="No verified forecasts found")
    return record

@router.put("/verify/{forecast_id}")
def update_forecast(forecast_id: int, forecast: VerifiedForecastCreate, db: Session = Depends(get_db)):
    record = db.query(VerifiedForecast).filter(VerifiedForecast.id == forecast_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Forecast not found")
    
    try:
        record.target_time = forecast.target_time
        record.dry_temp_c = forecast.dry_temp_c
        record.wind_speed_kts = forecast.wind_speed_kts
        record.wind_dir = forecast.wind_dir
        record.rh_percent = forecast.rh_percent
        record.clouds = forecast.clouds
        record.visibility = forecast.visibility
        record.qnh_hpa = forecast.qnh_hpa
        record.headwind_kts = forecast.headwind_kts
        record.crosswind_kts = forecast.crosswind_kts
        
        # Log to SystemLogs
        audit_log = SystemLogs(
            timestamp_utc=datetime.utcnow(),
            level="SUCCESS",
            component="Forecast_Verification",
            message=f"Forecaster updated verified forecast record (ID #{forecast_id}).",
            details=f"Updated Wind: {forecast.wind_speed_kts}kts / {forecast.wind_dir}°"
        )
        db.add(audit_log)
        
        db.commit()
        db.refresh(record)
        return {"message": "Verified forecast updated successfully", "id": record.id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update verified forecast: {str(e)}")
