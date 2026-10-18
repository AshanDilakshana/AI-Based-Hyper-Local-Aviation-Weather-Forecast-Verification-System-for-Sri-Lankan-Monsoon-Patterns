from fastapi import APIRouter, HTTPException
import pandas as pd
import os
import math
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))
from backend.data.database import SessionLocal
from backend.data.models import WeatherData

router = APIRouter(prefix="/live-metrology", tags=["Live Metrology Data API"])


@router.get("/current")
def get_current_live_weather():
    """
    Returns the most recent live METAR data from the database.
    """
    db = SessionLocal()
    try:
        latest_record = db.query(WeatherData).order_by(WeatherData.id.desc()).first()

        if not latest_record:
            raise HTTPException(
                status_code=500, detail="No weather data available in the database."
            )

        return {
            "timestamp_simulated": "live",
            "year": latest_record.year,
            "month": latest_record.month,
            "date": latest_record.date,
            "time_utc": str(latest_record.time_utc),
            "metar_speci": "METAR",
            "wind_dir": latest_record.wind_dir,
            "wind_speed_kts": latest_record.wind_speed_kts,
            "visibility": latest_record.visibility,
            "weather": latest_record.weather,
            "clouds": latest_record.clouds,
            "dry_temp_c": latest_record.dry_temp_c,
            "dew_point_c": latest_record.dew_point_c,
            "rh_percent": latest_record.rh_percent,
            "qnh_hpa": latest_record.qnh_hpa,
        }
    finally:
        db.close()


@router.get("/recent")
def get_recent_live_weather(limit: int = 10):
    """
    Returns the most recent `limit` METAR records from the database.
    """
    db = SessionLocal()
    try:
        records = (
            db.query(WeatherData).order_by(WeatherData.id.desc()).limit(limit).all()
        )
        result = []
        for r in records:
            result.append(
                {
                    "year": r.year,
                    "month": r.month,
                    "date": r.date,
                    "time_utc": str(r.time_utc),
                    "metar_speci": "METAR",
                    "wind_dir": r.wind_dir,
                    "wind_speed_kts": r.wind_speed_kts,
                    "visibility": r.visibility,
                    "weather": r.weather,
                    "clouds": r.clouds,
                    "dry_temp_c": r.dry_temp_c,
                    "dew_point_c": r.dew_point_c,
                    "rh_percent": r.rh_percent,
                    "qnh_hpa": r.qnh_hpa,
                }
            )
        return result
    finally:
        db.close()


from backend.live_metar_fetcher import fetch_and_store_live_metar


@router.post("/sync")
def force_sync_weather():
    """
    Manually triggers an immediate fetch of live METAR data from aviationweather.gov.
    """
    try:
        fetch_and_store_live_metar()
        return {"message": "Live METAR data successfully synchronized."}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to sync weather data: {str(e)}"
        )
