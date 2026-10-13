from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from pydantic import BaseModel
from typing import Optional, List
import pandas as pd
import io
import re

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
        raise HTTPException(
            status_code=404,
            detail="No historical weather data found to make predictions.",
        )

    wind_req = WindPredictionRequest(
        temperature=latest_weather.dry_temp_c,
        dew_point=latest_weather.dew_point_c,
        humidity=latest_weather.rh_percent,
        wind_dir=latest_weather.wind_dir,
        runway_heading=40,  # Default BIA runway 04
        time_utc=(
            str(latest_weather.time_utc).zfill(4) if latest_weather.time_utc else "0000"
        ),
        qnh_hpa=latest_weather.qnh_hpa,
    )

    import concurrent.futures
    from backend.data.database import SessionLocal
    from backend.data.models import ModelsForecast

    # Pre-create the unified forecast row to prevent concurrent insert race conditions
    if latest_weather and latest_weather.timestamp_utc:
        target_time = (latest_weather.timestamp_utc + timedelta(hours=3)).replace(minute=0, second=0, microsecond=0)
        existing_record = db.query(ModelsForecast).filter(ModelsForecast.target_time_utc == target_time).first()
        if not existing_record:
            new_forecast = ModelsForecast(target_time_utc=target_time)
            db.add(new_forecast)
            try:
                db.commit()
            except Exception:
                db.rollback()

    def run_wind():
        try:
            from backend.api.routers.wind_router import predict_wind_hybrid_3h
            return predict_wind_hybrid_3h(wind_req)
        except Exception as e:
            return {"error": f"Wind model failed: {str(e)}"}

    def run_temp():
        db_temp = SessionLocal()
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
                visibility=latest_weather.visibility,
            )
            return predict_temperature_pressure(temp_req, db_temp)
        except Exception as e:
            return {"error": f"Temp/Pressure model failed: {str(e)}"}
        finally:
            db_temp.close()

    def run_cloud():
        try:
            from backend.api.schemas import CloudVisibilityRequest
            from backend.api.routers.cloud_visibility_router import predict_cloud_visibility
            hour_val = (
                float(str(latest_weather.time_utc)[:2])
                if latest_weather.time_utc and len(str(latest_weather.time_utc)) >= 2
                else 12.0
            )
            cloud_req = CloudVisibilityRequest(
                temp=latest_weather.dry_temp_c,
                dew=latest_weather.dew_point_c,
                rh=latest_weather.rh_percent,
                qnh=latest_weather.qnh_hpa,
                wind=latest_weather.wind_speed_kts,
                month=latest_weather.month,
                hour=hour_val,
                wind_dir=latest_weather.wind_dir,
                weather_encoded=0.0,
            )
            return predict_cloud_visibility(cloud_req)
        except Exception as e:
            return {"error": f"Cloud model failed: {str(e)}"}

    def run_qnh():
        try:
            from backend.api.routers.qnh_dewpoint_router import predict_qnh_dewpoint_3h
            return predict_qnh_dewpoint_3h()
        except Exception as e:
            return {"error": f"QNH/Dewpoint model failed: {str(e)}"}

    wind_prediction = run_wind()
    temp_prediction = run_temp()
    cloud_visibility_prediction = run_cloud()
    qnh_dewpoint_prediction = run_qnh()

    return {
        "timestamp_utc": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "wind_forecast": wind_prediction,
        "temperature_pressure_forecast": temp_prediction,
        "cloud_visibility_forecast": cloud_visibility_prediction,
        "qnh_dewpoint_forecast": qnh_dewpoint_prediction,
    }


from backend.api.schemas import VerifiedForecastRequest
from backend.data.models import VerifiedForecast


@router.post("/verify")
def create_verified_forecast(
    req: VerifiedForecastRequest, db: Session = Depends(get_db)
):
    # Parse times
    target_dt = datetime.fromisoformat(req.target_time.replace("Z", "+00:00")).replace(
        tzinfo=None
    )
    created_dt = datetime.fromisoformat(req.created_at.replace("Z", "+00:00")).replace(
        tzinfo=None
    )

    vf = VerifiedForecast(
        target_time=target_dt,
        created_at=created_dt,
        dry_temp_c=req.dry_temp_c,
        wind_speed_kts=req.wind_speed_kts,
        wind_dir=req.wind_dir if req.wind_dir is not None else 0.0,
        rh_percent=req.rh_percent,
        clouds=req.clouds,
        visibility=req.visibility,
        qnh_hpa=req.qnh_hpa,
        headwind_kts=req.headwind_kts,
        crosswind_kts=req.crosswind_kts,
    )
    db.add(vf)
    db.commit()
    db.refresh(vf)
    return {"message": "Verified forecast saved", "id": vf.id}


@router.put("/verify/{id}")
def update_verified_forecast(
    id: int, req: VerifiedForecastRequest, db: Session = Depends(get_db)
):
    vf = db.query(VerifiedForecast).filter(VerifiedForecast.id == id).first()
    if not vf:
        raise HTTPException(status_code=404, detail="Not found")

    vf.target_time = datetime.fromisoformat(
        req.target_time.replace("Z", "+00:00")
    ).replace(tzinfo=None)
    vf.created_at = datetime.fromisoformat(
        req.created_at.replace("Z", "+00:00")
    ).replace(tzinfo=None)
    vf.dry_temp_c = req.dry_temp_c
    vf.wind_speed_kts = req.wind_speed_kts
    vf.wind_dir = req.wind_dir if req.wind_dir is not None else 0.0
    vf.rh_percent = req.rh_percent
    vf.clouds = req.clouds
    vf.visibility = req.visibility
    vf.qnh_hpa = req.qnh_hpa
    vf.headwind_kts = req.headwind_kts
    vf.crosswind_kts = req.crosswind_kts

    db.commit()
    return {"message": "Verified forecast updated"}


@router.get("/verified/latest")
def get_latest_verified_forecast(db: Session = Depends(get_db)):
    record = (
        db.query(VerifiedForecast).order_by(VerifiedForecast.target_time.desc()).first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="No verified forecasts found")
    return record


@router.get("/recent-verified")
def get_recent_verified_forecasts(limit: int = 12, db: Session = Depends(get_db)):
    records = (
        db.query(VerifiedForecast)
        .order_by(VerifiedForecast.target_time.desc())
        .limit(limit)
        .all()
    )
    return records


@router.post("/upload-csv")
async def upload_csv_forecasts(file: UploadFile = File(...)):
    if not (
        file.filename.endswith(".csv")
        or file.filename.endswith(".xlsx")
        or file.filename.endswith(".xls")
    ):
        raise HTTPException(
            status_code=400, detail="Only CSV or Excel files are allowed."
        )

    contents = await file.read()
    try:
        if file.filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(contents))
        else:
            df = pd.read_excel(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading file: {e}")

    # We expect columns roughly like:
    # 'UTC', 'Wind (deg/kt)', 'Air Temp (deg C)', 'QNH (hPa)', 'Remarks'
    # There might be a date somewhere, let's assume it's passed somehow or we use today's date if not in rows.
    # The user said date is in the CSV. Let's look for a 'Date' column or assume target_time is full datetime.

    # Let's map it dynamically.
    parsed_records = []

    # Get base date from first row or current date if not available
    # Wait, the user mentioned date is in the CSV. Let's assume there is a 'Date' column,
    # OR we just extract datetime.

    now = datetime.utcnow()
    base_date = now.date()

    for _, row in df.iterrows():
        # Fallbacks to avoid key errors
        def get_val(keys):
            for k in keys:
                if k in df.columns:
                    val = row[k]
                    return val if pd.notna(val) else None
            return None

        utc_val = get_val(["UTC", "Time (UTC)", "Time", "time"])
        if utc_val is None:
            continue

        wind_str = str(get_val(["Wind (deg/kt)", "Wind", "wind"]) or "")
        temp_val = get_val(["Air Temp (deg C)", "Temp", "temp"])
        qnh_val = get_val(["QNH (hPa)", "QNH", "qnh"])
        remarks_val = get_val(["Remarks", "remarks"])
        date_val = get_val(["Date", "date"])

        # Parse Wind
        wind_dir = 0.0
        wind_speed = 0.0
        if (
            wind_str
            and str(wind_str).strip()
            and str(wind_str).strip().lower() != "nan"
        ):
            clean_wind = str(wind_str).strip()
            
            if "/" in clean_wind:
                parts = clean_wind.split("/")
                if len(parts) == 2:
                    try:
                        wind_dir = float(parts[0].strip())
                        wind_speed = float(parts[1].strip())
                    except ValueError:
                        pass
            else:
                # Handle float representation from pandas (e.g., '3015.0')
                clean_wind = clean_wind.split(".")[0].strip()
                # Pad with leading zeros to make it at least 5 digits (e.g., '3015' -> '03015')
                clean_wind = clean_wind.zfill(5)
    
                match = re.search(r"^(\d{3})(\d{2,3})$", clean_wind)
                if match:
                    wind_dir = float(match.group(1))
                    wind_speed = float(match.group(2))

        # Parse Date and Time
        try:
            if date_val:
                dt_str = f"{date_val} {str(utc_val).zfill(4)}"
                target_time = pd.to_datetime(
                    dt_str, format="%Y-%m-%d %H%M", errors="coerce"
                )
                if pd.isna(target_time):
                    target_time = pd.to_datetime(dt_str, errors="coerce")
            else:
                # Use today's date and the UTC time
                time_str = str(int(utc_val)).zfill(4)
                target_time = datetime.strptime(
                    f"{base_date} {time_str}", "%Y-%m-%d %H%M"
                )
        except:
            target_time = now  # Fallback

        parsed_records.append(
            {
                "target_time": (
                    target_time.isoformat()
                    if hasattr(target_time, "isoformat")
                    else str(target_time)
                ),
                "dry_temp_c": float(temp_val) if temp_val is not None else None,
                "qnh_hpa": float(qnh_val) if qnh_val is not None else None,
                "wind_dir": wind_dir,
                "wind_speed_kts": wind_speed,
                "remarks": str(remarks_val) if remarks_val is not None else None,
            }
        )

    return {"records": parsed_records}


from backend.api.schemas import VerifiedForecastBulkRequest


@router.post("/bulk-verify")
def bulk_verify_forecasts(
    req: VerifiedForecastBulkRequest, db: Session = Depends(get_db)
):
    for forecast in req.forecasts:
        target_dt = datetime.fromisoformat(forecast.target_time.replace("Z", "+00:00")).replace(tzinfo=None)
        # Find if it already exists
        existing = (
            db.query(VerifiedForecast)
            .filter(VerifiedForecast.target_time == target_dt)
            .first()
        )

        if existing:
            # Update existing
            if forecast.dry_temp_c is not None:
                existing.dry_temp_c = forecast.dry_temp_c
            if forecast.wind_speed_kts is not None:
                existing.wind_speed_kts = forecast.wind_speed_kts
            if forecast.wind_dir is not None:
                existing.wind_dir = forecast.wind_dir
            if forecast.rh_percent is not None:
                existing.rh_percent = forecast.rh_percent
            if forecast.clouds is not None:
                existing.clouds = forecast.clouds
            if forecast.visibility is not None:
                existing.visibility = forecast.visibility
            if forecast.qnh_hpa is not None:
                existing.qnh_hpa = forecast.qnh_hpa
            if forecast.headwind_kts is not None:
                existing.headwind_kts = forecast.headwind_kts
            if forecast.crosswind_kts is not None:
                existing.crosswind_kts = forecast.crosswind_kts
            if hasattr(forecast, "remarks") and forecast.remarks is not None:
                existing.remarks = forecast.remarks
        else:
            # Insert new
            new_vf = VerifiedForecast(
                target_time=target_dt,
                dry_temp_c=forecast.dry_temp_c,
                wind_speed_kts=forecast.wind_speed_kts,
                wind_dir=forecast.wind_dir,
                rh_percent=forecast.rh_percent,
                clouds=forecast.clouds,
                visibility=forecast.visibility,
                qnh_hpa=forecast.qnh_hpa,
                headwind_kts=forecast.headwind_kts,
                crosswind_kts=forecast.crosswind_kts,
                remarks=getattr(forecast, "remarks", None),
            )
            db.add(new_vf)

    db.commit()
    return {
        "message": f"Successfully processed {len(req.forecasts)} verified forecasts."
    }
