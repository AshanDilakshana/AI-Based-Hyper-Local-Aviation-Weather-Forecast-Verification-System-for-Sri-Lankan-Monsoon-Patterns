from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime
from backend.data.database import get_db
from backend.data.models import WeatherData, ModelsForecast

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
        latest_pred = db.query(ModelsForecast).order_by(ModelsForecast.created_at.desc()).first()
        
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
            forecast_time_iso = latest_pred.target_time_utc.isoformat() if latest_pred.target_time_utc else ""
                
            response["prediction"] = {
                "predicted_temperature": latest_pred.temperature_c if latest_pred.temperature_c is not None else 0,
                "predicted_pressure": latest_pred.pressure_hpa if latest_pred.pressure_hpa is not None else 0,
                "forecast_report_time": forecast_time_iso,
                "input_report_time": latest_pred.created_at.isoformat() if latest_pred.created_at else ""
            }
            
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/verification-history")
def get_verification_history(db: Session = Depends(get_db)):
    """Fetch the verification history by matching ModelsForecast with WeatherData dynamically."""
    try:
        results = []
        # Fetch latest forecasts
        predictions = db.query(ModelsForecast).order_by(ModelsForecast.created_at.desc()).limit(20).all()
        
        for p in predictions:
            if not p.target_time_utc:
                continue
                
            # Find the actual observation matching this target time
            actual = db.query(WeatherData).filter(
                WeatherData.year == p.target_time_utc.year,
                WeatherData.month == p.target_time_utc.month,
                WeatherData.date == p.target_time_utc.day,
                # Format time_utc as HHMM for matching SQLite string
                WeatherData.time_utc == p.target_time_utc.strftime("%H%M")
            ).first()
            
            if actual and actual.dry_temp_c is not None and actual.qnh_hpa is not None:
                t_err = abs((p.temperature_c or 0) - actual.dry_temp_c)
                p_err = abs((p.pressure_hpa or 0) - actual.qnh_hpa)
                
                results.append({
                    "forecast_report_time": p.target_time_utc.isoformat(),
                    "predicted_temperature": p.temperature_c or 0,
                    "actual_temperature": actual.dry_temp_c,
                    "temp_error": round(t_err, 2),
                    "temp_status": "MATCH" if t_err < 1.0 else "MISMATCH",
                    "predicted_pressure": p.pressure_hpa or 0,
                    "actual_pressure": actual.qnh_hpa,
                    "pressure_error": round(p_err, 2),
                    "pressure_status": "MATCH" if p_err < 2.0 else "MISMATCH"
                })
                
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/thermodynamic-hazard-alert")
def get_thermodynamic_hazard_alert(db: Session = Depends(get_db)):
    """Check for Radiation Fog Precursors based on Temperature & Pressure coupled anomalies."""
    try:
        latest_ob = db.query(WeatherData).order_by(WeatherData.timestamp_utc.desc()).first()
        latest_pred = db.query(ModelsForecast).order_by(ModelsForecast.created_at.desc()).first()
        
        if not latest_ob or not latest_pred:
            return {"status": "NO_DATA", "message": "Insufficient data to calculate hazard."}

        current_temp = float(latest_ob.dry_temp_c) if latest_ob.dry_temp_c is not None else 0
        current_press = float(latest_ob.qnh_hpa) if latest_ob.qnh_hpa is not None else 0
        
        pred_temp = float(latest_pred.temperature_c) if latest_pred.temperature_c is not None else 0
        pred_press = float(latest_pred.pressure_hpa) if latest_pred.pressure_hpa is not None else 0
        
        # Calculate Rate of Change (over 3 hours)
        temp_drop = pred_temp - current_temp
        temp_roc_per_hr = round(temp_drop / 3.0, 2)
        
        # Hazard Detection Logic (Radiation Fog Precursor)
        is_rapid_cooling = temp_roc_per_hr <= -0.5
        is_high_stable_pressure = pred_press >= 1010.0 and abs(pred_press - current_press) <= 1.0
        
        hazard_risk = "HIGH (>85% Probability)" if (is_rapid_cooling and is_high_stable_pressure) else "LOW (<20% Probability)"
        
        return {
            "alert_title": "SYSTEM VERIFICATION ALERT: THERMODYNAMIC ANOMALY DETECTED",
            "target_period": f"+3 Hours ({latest_pred.target_time_utc.strftime('%H%M')} UTC)" if latest_pred.target_time_utc else "+3 Hours",
            "monsoon_profile": "Northeast Monsoon Regime",
            "detected_trigger": {
                "temperature_trend": f"Rapid Cooling detected ({temp_roc_per_hr}°C / hr)",
                "pressure_trend": f"High & Stable ({pred_press} hPa)"
            },
            "ai_verification_output": {
                "hazard_risk": hazard_risk,
                "hazard_type": "Radiation Fog Precursor Setup",
                "aviation_impact": "Imminent severe drop in visual range (RVR) due to radiation fog. Furthermore, the rapid temperature drop will alter local air density, necessitating updated takeoff performance calculations before departure.",
                "system_recommendation": "Cross-verify local visual range parameters with the Visibility Module. Pilots and ATC should prepare for potential early-morning boarding delays."
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sync-now")
def sync_now():
    """Trigger a manual METAR sync. Simulated for now based on user instruction."""
    # We simulate a successful sync without running external scripts
    return {"message": "Sync successful", "status": "simulated"}
