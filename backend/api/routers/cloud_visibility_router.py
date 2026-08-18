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


router = APIRouter(
    prefix="/predict",
    tags=["Cloud & Visibility Forecast"]
)


# MODEL PATH


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MODEL_PATH = os.path.abspath(
    os.path.join(BASE_DIR, "../../../Models/saved_models")
)


# =========================================================
# MODEL VARIABLES
# =========================================================

cloud_model = None
cloud_mapping = None

vis_model = None
vis_mapping = None


# =========================================================
# LOAD MODELS
# =========================================================

try:

    # -----------------------------------------------------
    # Load Cloud Model
    # -----------------------------------------------------

    cloud_model_path = os.path.join(
        MODEL_PATH,
        "xgb_cloud_model.pkl"
    )

    with open(cloud_model_path, "rb") as f:
        cloud_bundle = pickle.load(f)

    cloud_model = cloud_bundle["model"]
    cloud_mapping = cloud_bundle["mapping"]


    # -----------------------------------------------------
    # Load Visibility Model
    # -----------------------------------------------------

    visibility_model_path = os.path.join(
        MODEL_PATH,
        "xgb_visibility_model.pkl"
    )

    with open(visibility_model_path, "rb") as f:
        vis_bundle = pickle.load(f)

    vis_model = vis_bundle["model"]
    vis_mapping = vis_bundle["mapping"]


    print(
        "[SUCCESS] Cloud and Visibility XGBoost models loaded successfully!"
    )


except Exception as e:

    print(
        f"[ERROR] Model Loading Error in FastAPI Router: {e}"
    )


# =========================================================
# PREDICTION ENDPOINT
# =========================================================

@router.post(
    "",
    response_model=CloudVisibilityResponse
)
def predict_cloud_visibility(
    data: CloudVisibilityRequest
):

    # -----------------------------------------------------
    # Check Models
    # -----------------------------------------------------

    if cloud_model is None or vis_model is None:

        raise HTTPException(
            status_code=500,
            detail="Models failed to load on server startup."
        )


    try:

        # =================================================
        # FEATURE ENGINEERING
        # =================================================

        dew_point_depression = data.temp - data.dew

        temp_rh = data.temp * data.rh

        wind_rh = data.wind * data.rh

        pressure_wind = data.qnh * data.wind

        rh_squared = data.rh ** 2


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
            "Weather_Encoded"
        ]


        # =================================================
        # CREATE INPUT DATAFRAME
        # =================================================

        input_data = pd.DataFrame(
            [[
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
                data.weather_encoded
            ]],
            columns=feature_names
        )


        # =================================================
        # CLOUD PREDICTION
        # =================================================

        cloud_raw_pred = cloud_model.predict(
            input_data
        )[0]

        cloud_idx = int(
            np.clip(
                np.round(cloud_raw_pred),
                0,
                len(cloud_mapping) - 1
            )
        )


        # =================================================
        # VISIBILITY PREDICTION
        # =================================================

        vis_raw_pred = vis_model.predict(
            input_data
        )[0]

        vis_idx = int(
            np.clip(
                np.round(vis_raw_pred),
                0,
                len(vis_mapping) - 1
            )
        )


        # =================================================
        # FINAL RESPONSE
        # =================================================

        return CloudVisibilityResponse(
            visibility_prediction=int(
                vis_mapping[vis_idx]
            ),
            cloud_status=str(
                cloud_mapping[cloud_idx]
            )
        )


    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Prediction processing error: {e!s}"
        )