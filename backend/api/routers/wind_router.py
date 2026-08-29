from fastapi import APIRouter, HTTPException
import xgboost as xgb
import pandas as pd
import numpy as np
import os
from backend.api.schemas import WindPredictionRequest, WindPredictionResponse

router = APIRouter(prefix="/wind", tags=["Wind Prediction Models"])

# Load the AI Models globally for this router
# Corrected paths pointing to the 'Models' folder
import sys
import torch
from pytorch_forecasting import TemporalFusionTransformer

TFT_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../../Models/wind_models/TFT_3H")
)
if TFT_DIR not in sys.path:
    sys.path.append(TFT_DIR)


from tft_dataset_builder import load_and_prepare_data


def get_latest_tft_checkpoint(lightning_logs_dir):
    if not os.path.exists(lightning_logs_dir):
        return None
    version_dirs = [
        d
        for d in os.listdir(lightning_logs_dir)
        if os.path.isdir(os.path.join(lightning_logs_dir, d))
        and d.startswith("version_")
    ]
    if not version_dirs:
        return None
    version_dirs.sort(key=lambda x: int(x.split("_")[1]))
    valid_versions = []
    for d in version_dirs:
        ckpt_dir = os.path.join(lightning_logs_dir, d, "checkpoints")
        if os.path.exists(ckpt_dir) and os.listdir(ckpt_dir):
            valid_versions.append(d)
    if not valid_versions:
        return None
    latest_version_dir = os.path.join(lightning_logs_dir, valid_versions[-1])
    checkpoints_dir = os.path.join(latest_version_dir, "checkpoints")
    return os.path.join(checkpoints_dir, os.listdir(checkpoints_dir)[0])


MODEL_1H_PATH = os.path.join(
    os.path.dirname(__file__),
    "../../../Models/wind_models/1h prediction model/xgboost_wind_model_1h.json",
)
MODEL_3H_PATH = os.path.join(
    os.path.dirname(__file__),
    "../../../Models/wind_models/3h prediction model/xgboost_wind_model_3h.json",
)

model_1h = None
model_3h = None
model_tft_3h = None


def load_Wind_models():
    global model_1h, model_3h, model_tft_3h

    try:
        model_1h = xgb.XGBRegressor()
        model_1h.load_model(MODEL_1H_PATH)
    except Exception as e:
        print(f"Warning: Could not load 1H wind model. Trying backup. Error: {e}")
        try:
            backup_path = MODEL_1H_PATH.replace(".json", "_backup.json")
            model_1h = xgb.XGBRegressor()
            model_1h.load_model(backup_path)
            print("Loaded 1H BACKUP model.")
        except Exception:
            print("CRITICAL: Failed to load 1H model and backup.")
            model_1h = None

    try:
        model_3h = xgb.XGBRegressor()
        model_3h.load_model(MODEL_3H_PATH)
    except Exception as e:
        print(f"Warning: Could not load 3H wind model. Trying backup. Error: {e}")
        try:
            backup_path = MODEL_3H_PATH.replace(".json", "_backup.json")
            model_3h = xgb.XGBRegressor()
            model_3h.load_model(backup_path)
            print("Loaded 3H BACKUP model.")
        except Exception:
            print("CRITICAL: Failed to load 3H model and backup.")
            model_3h = None

    try:
        tft_logs_dir = os.path.join(TFT_DIR, "lightning_logs")
        tft_ckpt = get_latest_tft_checkpoint(tft_logs_dir)
        if tft_ckpt:
            model_tft_3h = TemporalFusionTransformer.load_from_checkpoint(tft_ckpt)
            print("Loaded TFT 3H model.")
        else:
            print("CRITICAL: Failed to find TFT 3H model checkpoint.")
            model_tft_3h = None
    except Exception as e:
        print(f"CRITICAL: Failed to load TFT 3H model. Error: {e}")
        model_tft_3h = None


load_Wind_models()


def calculate_aviation_winds(wind_speed: float, wind_dir: float, runway_heading: int):
    """Calculates Headwind and Crosswind for a specific runway."""
    angle_diff = np.radians(wind_dir - runway_heading)
    crosswind = wind_speed * np.sin(angle_diff)
    headwind = wind_speed * np.cos(angle_diff)
    return abs(crosswind), headwind


def suggest_best_runway(wind_speed: float, wind_dir: float):
    # Calculate for RWY 04 (heading 40)
    crosswind_04, headwind_04 = calculate_aviation_winds(wind_speed, wind_dir, 40)
    # Calculate for RWY 22 (heading 220)
    crosswind_22, headwind_22 = calculate_aviation_winds(wind_speed, wind_dir, 220)

    # We prefer the runway with the highest headwind for safe takeoff
    if headwind_22 > headwind_04:
        return 220, abs(crosswind_22), headwind_22, "RWY 22"
    else:
        return 40, abs(crosswind_04), headwind_04, "RWY 04"


def get_alert_status(crosswind: float, timeframe_str: str):
    status = "SAFE"
    message = (
        f"Forecast for {timeframe_str}: Crosswind components are within normal limits."
    )
    if crosswind > 15:
        status = "WARNING"
        message = (
            f"Forecast for {timeframe_str}: High crosswind likely! Plan contingencies."
        )
    if crosswind > 25:
        status = "DANGER"
        message = f"Forecast for {timeframe_str}: Severe crosswind. Exceeds standard operating limits."
    return status, message


from backend.data.database import SessionLocal
from backend.data.models import WeatherData, ModelsForecast
import sys
import datetime

# Ensure Models directory is accessible
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))
from preprocessing_and_feature_engineering.wind_prediction_model.unified_pipeline import (
    UnifiedWeatherPipeline,
)


def get_historical_dataframe(db_session):
    # Fetch 13 records: 12 for past data + 1 for current live data
    records = (
        db_session.query(WeatherData).order_by(WeatherData.id.desc()).limit(13).all()
    )
    records.reverse()

    data = []
    for i, r in enumerate(records):
        is_latest = i == len(records) - 1
        data.append(
            {
                "Year": r.year,
                "Month": r.month,
                "Date": r.date,
                "Time(UTC)": str(r.time_utc).zfill(4) if r.time_utc else "0000",
                "Wind Dir": r.wind_dir,
                "Wind speed(Kts)": (
                    None if is_latest else r.wind_speed_kts
                ),  # Hide target for the row we are predicting
                "Dry Temp(0C)": r.dry_temp_c,
                "Dew point(0C)": r.dew_point_c,
                "RH(%)": r.rh_percent,
                "QNH(hPa)": r.qnh_hpa,
            }
        )

    return pd.DataFrame(data)


def calculate_target_datetime(df_window, forecast_hours):
    last_row = df_window.iloc[-1]
    time_str = (
        str(last_row["Time(UTC)"]).zfill(4)
        if pd.notnull(last_row["Time(UTC)"])
        else "0000"
    )
    year = int(last_row["Year"]) if pd.notnull(last_row["Year"]) else 2026
    month = int(last_row["Month"]) if pd.notnull(last_row["Month"]) else 1
    date = int(last_row["Date"]) if pd.notnull(last_row["Date"]) else 1

    dt = datetime.datetime(year, month, date, int(time_str[:2]), int(time_str[2:]))
    dt_target = dt + datetime.timedelta(hours=forecast_hours)
    return dt_target


@router.post("/predict/1h", response_model=WindPredictionResponse)
def predict_wind_1h(request: WindPredictionRequest):
    if model_1h is None:
        raise HTTPException(status_code=500, detail="1H Wind AI Model is not loaded.")

    db = SessionLocal()
    try:
        df_window = get_historical_dataframe(db)
    finally:
        db.close()

    pipeline = UnifiedWeatherPipeline(forecast_hours=1)
    features = pipeline.process_inference_data(df_window)

    # Ensure ordering matches
    expected_cols = pipeline.required_features
    features_ordered = features[expected_cols]

    raw_wind_dir = df_window.iloc[-1]["Wind Dir"]
    current_wind_dir = float(raw_wind_dir) if pd.notnull(raw_wind_dir) else 0.0

    predicted_wind_speed = float(model_1h.predict(features_ordered)[0])
    best_heading, crosswind, headwind, runway_name = suggest_best_runway(
        predicted_wind_speed, current_wind_dir
    )
    status, message = get_alert_status(crosswind, "1 hour ahead")

    # Save to Database for Verification
    dt_target = calculate_target_datetime(df_window, forecast_hours=1)

    db = SessionLocal()
    try:
        unified_dt_target = dt_target.replace(minute=0, second=0, microsecond=0)
        unified_record = (
            db.query(ModelsForecast)
            .filter(ModelsForecast.target_time_utc == unified_dt_target)
            .first()
        )
        if not unified_record:
            unified_record = ModelsForecast(target_time_utc=unified_dt_target)
            db.add(unified_record)

        unified_record.wind_speed_kts = predicted_wind_speed
        unified_record.wind_dir = current_wind_dir
        db.commit()
    except Exception as e:
        print(f"Failed to save prediction record: {e}")
    finally:
        db.close()

    return WindPredictionResponse(
        predicted_wind_speed_kts=round(predicted_wind_speed, 2),
        wind_dir=current_wind_dir,
        headwind_kts=round(headwind, 2),
        crosswind_kts=round(crosswind, 2),
        runway=runway_name,
        status=status,
        message=message,
    )


@router.post("/predict/3h", response_model=WindPredictionResponse)
def predict_wind_3h(request: WindPredictionRequest):
    if model_3h is None:
        raise HTTPException(status_code=500, detail="3H Wind AI Model is not loaded.")

    if request.time_utc is None or request.qnh_hpa is None:
        raise HTTPException(
            status_code=400,
            detail="time_utc and qnh_hpa are required for the 3H model.",
        )

    db = SessionLocal()
    try:
        df_window = get_historical_dataframe(db)
    finally:
        db.close()

    pipeline = UnifiedWeatherPipeline(forecast_hours=3)
    features = pipeline.process_inference_data(df_window)

    expected_cols = pipeline.required_features
    features_ordered = features[expected_cols]

    raw_wind_dir = df_window.iloc[-1]["Wind Dir"]
    current_wind_dir = float(raw_wind_dir) if pd.notnull(raw_wind_dir) else 0.0

    predicted_wind_speed = float(model_3h.predict(features_ordered)[0])
    best_heading, crosswind, headwind, runway_name = suggest_best_runway(
        predicted_wind_speed, current_wind_dir
    )
    status, message = get_alert_status(crosswind, "3 hours ahead")

    # Save to Database for Verification
    dt_target = calculate_target_datetime(df_window, forecast_hours=3)

    db = SessionLocal()
    try:
        unified_dt_target = dt_target.replace(minute=0, second=0, microsecond=0)
        unified_record = (
            db.query(ModelsForecast)
            .filter(ModelsForecast.target_time_utc == unified_dt_target)
            .first()
        )
        if not unified_record:
            unified_record = ModelsForecast(target_time_utc=unified_dt_target)
            db.add(unified_record)

        unified_record.wind_speed_kts = predicted_wind_speed
        unified_record.wind_dir = current_wind_dir
        db.commit()
    except Exception as e:
        print(f"Failed to save prediction record: {e}")
    finally:
        db.close()

    return WindPredictionResponse(
        predicted_wind_speed_kts=round(predicted_wind_speed, 2),
        wind_dir=current_wind_dir,
        headwind_kts=round(headwind, 2),
        crosswind_kts=round(crosswind, 2),
        runway=runway_name,
        status=status,
        message=message,
    )


@router.post("/predict/tft_3h", response_model=WindPredictionResponse)
def predict_wind_tft_3h(request: WindPredictionRequest):
    if model_tft_3h is None:
        raise HTTPException(
            status_code=500, detail="TFT 3H Wind AI Model is not loaded."
        )

    if request.time_utc is None or request.qnh_hpa is None:
        raise HTTPException(
            status_code=400,
            detail="time_utc and qnh_hpa are required for the 3H model.",
        )

    from backend.data.database import engine

    try:
        df_tft = load_and_prepare_data(engine=engine).tail(96).reset_index(drop=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load data for TFT: {e}")

    # Passing the dataframe directly to predict() automatically creates the future targets
    tft_preds = model_tft_3h.predict(
        df_tft, mode="prediction", trainer_kwargs={"logger": False}
    )
    predicted_wind_speed = float(tft_preds[0][2].item())

    raw_wind_dir = df_tft.iloc[-1]["wind_dir"]
    current_wind_dir = float(raw_wind_dir) if pd.notnull(raw_wind_dir) else 0.0

    best_heading, crosswind, headwind, runway_name = suggest_best_runway(
        predicted_wind_speed, current_wind_dir
    )
    status, message = get_alert_status(crosswind, "3 hours ahead (TFT)")

    # Save to Database for Verification
    db = SessionLocal()
    try:
        df_window = get_historical_dataframe(db)
        dt_target = calculate_target_datetime(df_window, forecast_hours=3)
        unified_dt_target = dt_target.replace(minute=0, second=0, microsecond=0)
        unified_record = (
            db.query(ModelsForecast)
            .filter(ModelsForecast.target_time_utc == unified_dt_target)
            .first()
        )
        if not unified_record:
            unified_record = ModelsForecast(target_time_utc=unified_dt_target)
            db.add(unified_record)

        unified_record.wind_speed_kts = predicted_wind_speed
        unified_record.wind_dir = current_wind_dir
        db.commit()
    except Exception as e:
        print(f"Failed to save prediction record: {e}")
    finally:
        db.close()

    return WindPredictionResponse(
        predicted_wind_speed_kts=round(predicted_wind_speed, 2),
        wind_dir=current_wind_dir,
        headwind_kts=round(headwind, 2),
        crosswind_kts=round(crosswind, 2),
        runway=runway_name,
        status=status,
        message=message,
    )


@router.post("/predict/hybrid_3h", response_model=WindPredictionResponse)
def predict_wind_hybrid_3h(request: WindPredictionRequest):
    if model_3h is None or model_tft_3h is None:
        raise HTTPException(
            status_code=500, detail="Models required for Hybrid 3H are not loaded."
        )

    if request.time_utc is None or request.qnh_hpa is None:
        raise HTTPException(
            status_code=400,
            detail="time_utc and qnh_hpa are required for the 3H model.",
        )

    # TFT Predict
    from backend.data.database import engine

    try:
        df_tft = load_and_prepare_data(engine=engine).tail(96).reset_index(drop=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load data for TFT: {e}")

    tft_preds = model_tft_3h.predict(
        df_tft, mode="prediction", trainer_kwargs={"logger": False}
    )
    tft_pred_value = float(tft_preds[0][2].item())

    # XGBoost Predict
    db = SessionLocal()
    try:
        df_window = get_historical_dataframe(db)
    finally:
        db.close()

    pipeline = UnifiedWeatherPipeline(forecast_hours=3)
    features = pipeline.process_inference_data(df_window)
    expected_cols = pipeline.required_features
    features_ordered = features[expected_cols]

    xgb_pred_value = float(model_3h.predict(features_ordered)[0])

    # Hybrid Predict (Average)
    predicted_wind_speed = (tft_pred_value + xgb_pred_value) / 2.0

    raw_wind_dir = df_window.iloc[-1]["Wind Dir"]
    current_wind_dir = float(raw_wind_dir) if pd.notnull(raw_wind_dir) else 0.0

    best_heading, crosswind, headwind, runway_name = suggest_best_runway(
        predicted_wind_speed, current_wind_dir
    )
    status, message = get_alert_status(crosswind, "3 hours ahead (Hybrid)")

    # Save to Database for Verification
    dt_target = calculate_target_datetime(df_window, forecast_hours=3)

    db = SessionLocal()
    try:
        unified_dt_target = dt_target.replace(minute=0, second=0, microsecond=0)
        unified_record = (
            db.query(ModelsForecast)
            .filter(ModelsForecast.target_time_utc == unified_dt_target)
            .first()
        )
        if not unified_record:
            unified_record = ModelsForecast(target_time_utc=unified_dt_target)
            db.add(unified_record)

        unified_record.wind_speed_kts = predicted_wind_speed
        unified_record.wind_dir = current_wind_dir

        db.commit()
    except Exception as e:
        print(f"Failed to save prediction record: {e}")
    finally:
        db.close()

    return WindPredictionResponse(
        predicted_wind_speed_kts=round(predicted_wind_speed, 2),
        wind_dir=current_wind_dir,
        headwind_kts=round(headwind, 2),
        crosswind_kts=round(crosswind, 2),
        runway=runway_name,
        status=status,
        message=message,
    )
