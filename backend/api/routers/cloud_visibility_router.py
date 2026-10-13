import os
import pickle
import sys

import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "../../.."))
BACKEND_DIR = os.path.abspath(os.path.join(BASE_DIR, "../.."))
API_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))

for path in [PROJECT_ROOT, BACKEND_DIR, API_DIR]:
    if path not in sys.path:
        sys.path.insert(0, path)


# IMPORT SCHEMAS


try:
    from backend.api.schemas import CloudVisibilityRequest, CloudVisibilityResponse
except ImportError:
    try:
        from api.schemas import CloudVisibilityRequest, CloudVisibilityResponse
    except ImportError:
        from schemas import (  # type: ignore[import-not-found]
            CloudVisibilityRequest,
            CloudVisibilityResponse,
        )


# ROUTER


router = APIRouter(prefix="/predict", tags=["Cloud & Visibility Forecast"])


# MODEL PATH


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MODEL_PATH = os.path.abspath(
    os.path.join(BASE_DIR, "../../../Models/cloud_visibility_models")
)


# =========================================================
# MODEL VARIABLES
# =========================================================

cloud_model = None
cloud_mapping = None
cloud_type_model = None
cloud_height_model = None
cloud_type_mapping = None

vis_model = None
vis_mapping = None


# =========================================================
# LOAD MODELS
# =========================================================


def load_models():
    """
    Loads or reloads the models into memory.
    Called on startup and after automated retraining.
    """
    global cloud_model, cloud_mapping, cloud_type_model, cloud_height_model, cloud_type_mapping, vis_model, vis_mapping

    # -----------------------------------------------------
    # Load Cloud Model with Fallback
    # -----------------------------------------------------
    cloud_primary = os.path.join(MODEL_PATH, "xgb_cloud_model.pkl")
    cloud_backup = os.path.join(MODEL_PATH, "xgb_cloud_model_backup.pkl")

    try:
        if os.path.exists(cloud_primary):
            with open(cloud_primary, "rb") as f:
                cloud_bundle = pickle.load(f)
            if 'type_model' in cloud_bundle:
                cloud_type_model = cloud_bundle['type_model']
                cloud_height_model = cloud_bundle['height_model']
                cloud_type_mapping = cloud_bundle['type_mapping']
            else:
                cloud_model = cloud_bundle["model"]
                cloud_mapping = cloud_bundle["mapping"]
            print("[SUCCESS] Loaded Primary Cloud XGBoost Model.")
        else:
            raise FileNotFoundError(f"Primary Cloud model not found at {cloud_primary}")
    except Exception as e:
        print(
            f"[WARNING] Failed to load primary Cloud model: {e}. Attempting backup..."
        )
        try:
            if os.path.exists(cloud_backup):
                with open(cloud_backup, "rb") as f:
                    cloud_bundle = pickle.load(f)
                if 'type_model' in cloud_bundle:
                    cloud_type_model = cloud_bundle['type_model']
                    cloud_height_model = cloud_bundle['height_model']
                    cloud_type_mapping = cloud_bundle['type_mapping']
                else:
                    cloud_model = cloud_bundle["model"]
                    cloud_mapping = cloud_bundle["mapping"]
                print("[SUCCESS] Loaded Backup Cloud XGBoost Model.")
            else:
                print("[ERROR] No Backup Cloud model found.")
        except Exception as backup_e:
            print(f"[ERROR] Failed to load backup Cloud model: {backup_e}")

    # -----------------------------------------------------
    # Load Visibility Model with Fallback
    # -----------------------------------------------------
    visibility_primary = os.path.join(MODEL_PATH, "xgb_visibility_model.pkl")
    visibility_backup = os.path.join(MODEL_PATH, "xgb_visibility_model_backup.pkl")

    try:
        if os.path.exists(visibility_primary):
            with open(visibility_primary, "rb") as f:
                vis_bundle = pickle.load(f)
            vis_model = vis_bundle["model"]
            vis_mapping = vis_bundle["mapping"]
            print("[SUCCESS] Loaded Primary Visibility XGBoost Model.")
        else:
            raise FileNotFoundError(
                f"Primary Visibility model not found at {visibility_primary}"
            )
    except Exception as e:
        print(
            f"[WARNING] Failed to load primary Visibility model: {e}. Attempting backup..."
        )
        try:
            if os.path.exists(visibility_backup):
                with open(visibility_backup, "rb") as f:
                    vis_bundle = pickle.load(f)
                vis_model = vis_bundle["model"]
                vis_mapping = vis_bundle["mapping"]
                print("[SUCCESS] Loaded Backup Visibility XGBoost Model.")
            else:
                print("[ERROR] No Backup Visibility model found.")
        except Exception as backup_e:
            print(f"[ERROR] Failed to load backup Visibility model: {backup_e}")


# Initial load on module import
load_models()


# =========================================================
# PREDICTION ENDPOINT
# =========================================================


@router.post("", response_model=CloudVisibilityResponse)
def predict_cloud_visibility(data: CloudVisibilityRequest):

    # -----------------------------------------------------
    # Check Models
    # -----------------------------------------------------

    if (cloud_model is None and cloud_type_model is None) or vis_model is None:

        raise HTTPException(
            status_code=500, detail="Models failed to load on server startup."
        )

    try:

        # =================================================
        # FETCH LIVE DATA FROM DATABASE
        # =================================================
        from backend.data.database import engine
        from sqlalchemy import text

        try:
            with engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT month, time_utc, wind_dir, wind_speed_kts, dry_temp_c, dew_point_c, rh_percent, qnh_hpa, timestamp_utc
                    FROM weather_data 
                    ORDER BY timestamp_utc DESC LIMIT 1
                """))
                row = result.fetchone()
                latest_timestamp_utc = None

            if row:
                latest_timestamp_utc = row[8]
                # Override payload with live database values
                data.month = float(row[0]) if row[0] is not None else data.month

                time_utc_str = str(row[1]) if row[1] is not None else ""
                data.hour = (
                    float(int(time_utc_str) // 100)
                    if time_utc_str.isdigit()
                    else data.hour
                )

                data.wind_dir = float(row[2]) if row[2] is not None else data.wind_dir
                data.wind = float(row[3]) if row[3] is not None else data.wind
                data.temp = float(row[4]) if row[4] is not None else data.temp
                data.dew = float(row[5]) if row[5] is not None else data.dew
                data.rh = float(row[6]) if row[6] is not None else data.rh
                data.qnh = float(row[7]) if row[7] is not None else data.qnh

                print(
                    f"[INFO] Fetched live data from DB for prediction: Temp={data.temp}, Wind={data.wind}"
                )
        except Exception as db_e:
            print(
                f"[WARNING] Could not fetch live data from DB, using payload fallback: {db_e}"
            )
            
        data.wind_dir = float(data.wind_dir) if data.wind_dir is not None else 0.0
        data.wind = float(data.wind) if data.wind is not None else 0.0
        data.temp = float(data.temp) if data.temp is not None else 30.0
        data.dew = float(data.dew) if data.dew is not None else 25.0
        data.rh = float(data.rh) if data.rh is not None else 75.0
        data.qnh = float(data.qnh) if data.qnh is not None else 1010.0
        data.month = float(data.month) if data.month is not None else 6.0
        data.hour = float(data.hour) if data.hour is not None else 12.0
        data.weather_encoded = float(data.weather_encoded) if data.weather_encoded is not None else 0.0

        # =================================================
        # FEATURE ENGINEERING
        # =================================================

        dew_point_depression = data.temp - data.dew

        temp_rh = data.temp * data.rh

        wind_rh = data.wind * data.rh

        pressure_wind = data.qnh * data.wind

        rh_squared = data.rh**2

        # =================================================
        # FEATURE NAMES
        # =================================================

        feature_names = [
            "Month",
            "Hour",
            "Wind Dir.",
            "Wind speed(Kts)",
            "Dry tem(0C)",
            "Dew point(0C)",
            "RH(%)",
            "QNH (hPa)",
            "Dew_Point_Depression",
            "Temp_RH",
            "Wind_RH",
            "Pressure_Wind",
            "RH_Squared",
            "Weather_Encoded",
        ]

        # =================================================
        # CREATE INPUT DATAFRAME
        # =================================================

        input_data = pd.DataFrame(
            [
                [
                    data.month,
                    data.hour,
                    data.wind_dir,
                    data.wind,
                    data.temp,
                    data.dew,
                    data.rh,
                    data.qnh,
                    dew_point_depression,
                    temp_rh,
                    wind_rh,
                    pressure_wind,
                    rh_squared,
                    data.weather_encoded,
                ]
            ],
            columns=feature_names,
        )

        # =================================================
        # CLOUD PREDICTION
        # =================================================

        if cloud_type_model is not None and cloud_height_model is not None:
            type_raw = cloud_type_model.predict(input_data)[0]
            type_idx = int(np.clip(np.round(type_raw), 0, len(cloud_type_mapping) - 1))
            cloud_type = str(cloud_type_mapping[type_idx])
            
            height_raw = cloud_height_model.predict(input_data)[0]
            cloud_height = int(np.clip(np.round(height_raw), 0, 999))
            
            if cloud_type in ['NSC', 'SKC', 'CLR', 'CAVOK', 'NIL']:
                cloud_status = cloud_type
            else:
                cloud_status = f"{cloud_type}{cloud_height:03d}"
        else:
            cloud_raw_pred = cloud_model.predict(input_data)[0]
            cloud_idx = int(np.clip(np.round(cloud_raw_pred), 0, len(cloud_mapping) - 1))
            cloud_status = str(cloud_mapping[cloud_idx])

        # =================================================
        # VISIBILITY PREDICTION
        # =================================================

        vis_raw_pred = vis_model.predict(input_data)[0]

        vis_idx = int(np.clip(np.round(vis_raw_pred), 0, len(vis_mapping) - 1))

        # =================================================
        # SAVE TO UNIFIED FORECAST TABLE
        # =================================================

        from backend.data.database import SessionLocal
        from backend.data.models import ModelsForecast
        from datetime import datetime, timedelta

        db = SessionLocal()
        try:
            if "latest_timestamp_utc" in locals() and latest_timestamp_utc:
                target_time = (latest_timestamp_utc + timedelta(hours=3)).replace(
                    minute=0, second=0, microsecond=0
                )
            else:
                target_time = (datetime.utcnow() + timedelta(hours=3)).replace(
                    minute=0, second=0, microsecond=0
                )

            unified_record = (
                db.query(ModelsForecast)
                .filter(ModelsForecast.target_time_utc == target_time)
                .first()
            )
            if not unified_record:
                unified_record = ModelsForecast(target_time_utc=target_time)
                db.add(unified_record)

            unified_record.visibility = float(vis_mapping[vis_idx])
            unified_record.clouds = cloud_status
            db.add(unified_record)
            db.commit()
            print(f"[SUCCESS] Cloud/Visibility Prediction saved to DB for target time: {target_time}")
        except Exception as db_e:
            print(f"[ERROR] Failed to save to ModelsForecast: {db_e}")
        finally:
            db.close()

        # =================================================
        # FINAL RESPONSE
        # =================================================

        return CloudVisibilityResponse(
            visibility_prediction=int(float(vis_mapping[vis_idx])),
            cloud_status=cloud_status,
        )

    except Exception as e:

        raise HTTPException(
            status_code=500, detail=f"Prediction processing error: {e!s}"
        )
