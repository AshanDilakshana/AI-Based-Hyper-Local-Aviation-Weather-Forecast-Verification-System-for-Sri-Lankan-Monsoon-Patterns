from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime
from backend.data.database import get_db
from backend.data.models import WeatherData, PredictionRecord, VerifiedForecast

router = APIRouter(prefix="/api", tags=["Dashboard API"])

@router.get("/recent-observations")
def get_recent_observations(db: Session = Depends(get_db)):
    """Fetch the most recent 10 records from the weather_data table."""
    try:
        records = db.query(WeatherData).order_by(WeatherData.timestamp_utc.desc()).limit(10).all()
        # Sort oldest to newest for the graph
        records.reverse()
        
        results = []
        for r in records:
            results.append({
                "report_time": r.timestamp_utc.isoformat() if r.timestamp_utc else "",
                "temperature": r.dry_temp_c if r.dry_temp_c is not None else 0,
                "pressure": r.qnh_hpa if r.qnh_hpa is not None else 0,
                "humidity": r.rh_percent if r.rh_percent is not None else 0,
                "wind_speed": r.wind_speed_kts if r.wind_speed_kts is not None else 0,
                "wind_direction": r.wind_dir if r.wind_dir is not None else 0,
                "visibility": r.visibility if r.visibility is not None else 0,
                "raw_ob": r.weather if r.weather else "METAR VCBI SIMULATED"
            })
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/latest-forecast")
def get_latest_forecast(db: Session = Depends(get_db)):
    """Fetch the latest prediction and the latest observation."""
    try:
        latest_ob = db.query(WeatherData).order_by(WeatherData.timestamp_utc.desc()).first()
        latest_pred = db.query(PredictionRecord).order_by(PredictionRecord.created_at.desc()).first()
        
        response = {}
        
        if latest_ob:
            response["observation"] = {
                "report_time": latest_ob.timestamp_utc.isoformat() if latest_ob.timestamp_utc else "",
                "temperature": latest_ob.dry_temp_c if latest_ob.dry_temp_c is not None else 0,
                "pressure": latest_ob.qnh_hpa if latest_ob.qnh_hpa is not None else 0,
                "humidity": latest_ob.rh_percent if latest_ob.rh_percent is not None else 0,
                "wind_speed": latest_ob.wind_speed_kts if latest_ob.wind_speed_kts is not None else 0,
                "wind_direction": latest_ob.wind_dir if latest_ob.wind_dir is not None else 0,
                "visibility": latest_ob.visibility if latest_ob.visibility is not None else 0,
            }
            
        if latest_pred:
            # Reconstruct the target time from the prediction record components
            try:
                target_dt = datetime(
                    latest_pred.target_year, 
                    latest_pred.target_month, 
                    latest_pred.target_date, 
                    int(latest_pred.target_time_utc[:2]), 
                    int(latest_pred.target_time_utc[2:])
                )
                forecast_time_iso = target_dt.isoformat()
            except:
                forecast_time_iso = latest_pred.created_at.isoformat() if latest_pred.created_at else ""
                
            response["prediction"] = {
                "predicted_temperature": latest_pred.predicted_temperature_c if latest_pred.predicted_temperature_c is not None else 0,
                "predicted_pressure": latest_pred.predicted_pressure_hpa if latest_pred.predicted_pressure_hpa is not None else 0,
                "forecast_report_time": forecast_time_iso,
                "input_report_time": latest_pred.created_at.isoformat() if latest_pred.created_at else ""
            }
            
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/verification-history")
def get_verification_history(db: Session = Depends(get_db)):
    """Fetch the verification history by joining predictions and actuals."""
    try:
        # Check if we have data in the VerifiedForecast table
        verified = db.query(VerifiedForecast).order_by(VerifiedForecast.target_time.desc()).limit(20).all()
        
        # In a fully fleshed out system, this table is populated by a background cron job.
        # If it's empty, we can just return a simulated history or match on the fly for demonstration.
        
        results = []
        for v in verified:
            # Assuming we need to mock or calculate the prediction vs actual here since 
            # VerifiedForecast mostly contains actuals, wait, let's look at models.py...
            # Actually, VerifiedForecast in models.py only has actual metrics:
            # dry_temp_c, wind_speed_kts, etc. and target_time.
            # We would need to join PredictionRecord to get the predicted values.
            pass
            
        # Let's dynamically match predictions with observations that occurred at the target time
        predictions = db.query(PredictionRecord).order_by(PredictionRecord.created_at.desc()).limit(20).all()
        
        for p in predictions:
            try:
                target_dt = datetime(
                    p.target_year, p.target_month, p.target_date, 
                    int(p.target_time_utc[:2]), int(p.target_time_utc[2:])
                )
                
                # Find the actual observation closest to this target time
                # In SQLite, we can just fetch the observation matching this year, month, date, time_utc
                # or just the closest one by timestamp
                actual = db.query(WeatherData).filter(
                    WeatherData.year == p.target_year,
                    WeatherData.month == p.target_month,
                    WeatherData.date == p.target_date,
                    WeatherData.time_utc == p.target_time_utc
                ).first()
                
                if actual and actual.dry_temp_c is not None and actual.qnh_hpa is not None:
                    # We have a match!
                    t_err = abs((p.predicted_temperature_c or 0) - actual.dry_temp_c)
                    p_err = abs((p.predicted_pressure_hpa or 0) - actual.qnh_hpa)
                    
                    results.append({
                        "forecast_report_time": target_dt.isoformat(),
                        "predicted_temperature": p.predicted_temperature_c or 0,
                        "actual_temperature": actual.dry_temp_c,
                        "temp_error": t_err,
                        "temp_status": "MATCH" if t_err < 1.0 else "MISMATCH",
                        "predicted_pressure": p.predicted_pressure_hpa or 0,
                        "actual_pressure": actual.qnh_hpa,
                        "pressure_error": p_err,
                        "pressure_status": "MATCH" if p_err < 2.0 else "MISMATCH"
                    })
            except:
                continue
                
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sync-now")
def sync_now():
    """Trigger a manual METAR sync. Simulated for now based on user instruction."""
    # We simulate a successful sync without running external scripts
    return {"message": "Sync successful", "status": "simulated"}
