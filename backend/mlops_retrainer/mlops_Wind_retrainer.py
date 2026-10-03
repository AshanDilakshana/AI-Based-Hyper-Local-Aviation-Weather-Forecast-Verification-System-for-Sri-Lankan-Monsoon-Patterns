import os
import sys
import pandas as pd
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from backend.data.database import SessionLocal
from backend.data.models import WeatherData, SystemLogs
from preprocessing_and_feature_engineering.wind_prediction_model.unified_pipeline import (
    UnifiedWeatherPipeline,
)
from Models.wind_models.wind_trainer import train_for_mlops, evaluate_old_model
from backend.mlops_retrainer.sync_training_data import sync_training_data


def get_all_historical_data(db_session):
    records = db_session.query(WeatherData).order_by(WeatherData.id.asc()).all()
    data = []
    for r in records:
        data.append(
            {
                "Year": r.year,
                "Month": r.month,
                "Date": r.date,
                "Time(UTC)": str(r.time_utc).zfill(4) if r.time_utc else "0000",
                "Wind Dir": r.wind_dir,
                "Wind speed(Kts)": r.wind_speed_kts,
                "Dry Temp(0C)": r.dry_temp_c,
                "Dew point(0C)": r.dew_point_c,
                "RH(%)": r.rh_percent,
                "QNH(hPa)": r.qnh_hpa,
            }
        )
    return pd.DataFrame(data)


def log_event(db_session, level, component, message, details=None):
    try:
        log = SystemLogs(level=level, component=component, message=message, details=details)
        db_session.add(log)
        db_session.commit()
    except Exception as e:
        db_session.rollback()
        print(f"Failed to write log to DB: {e}")
    print(f"[{level}] {component}: {message}")


def retrain_model_pipeline(forecast_hours, target_col, model_dir, model_filename):
    db = SessionLocal()
    component = f"MLOps_{forecast_hours}H"

    try:
        log_event(db, "INFO", component, "Started Retraining Process")

        df_raw = get_all_historical_data(db)
        if len(df_raw) < 100:
            log_event(
                db, "WARNING", component, "Not enough data to retrain (<100 rows)."
            )
            return False, "Not enough data"

        pipeline = UnifiedWeatherPipeline(forecast_hours=forecast_hours)
        X, y = pipeline.process_training_data(df_raw)

        df_processed = X.copy()
        df_processed[target_col] = y

        if df_processed.empty:
            log_event(db, "ERROR", component, "Processed data is empty.")
            return False, "Processing failed"

        log_event(db, "INFO", component, "Training New Model...")
        new_model, new_mae, X_test, y_test = train_for_mlops(df_processed, target_col)

        model_path = os.path.join(model_dir, model_filename)
        old_mae = evaluate_old_model(model_path, X_test, y_test)

        if old_mae is None:
            if new_mae < 2.3:
                log_event(
                    db,
                    "INFO",
                    component,
                    f"No existing model found. Saving new model. MAE: {new_mae:.2f}",
                )
                os.makedirs(model_dir, exist_ok=True)
                new_model.save_model(model_path)
                log_event(db, "SUCCESS", component, "New model deployed successfully.")
                return True, "Model Deployed"
            else:
                log_event(
                    db,
                    "WARNING",
                    component,
                    f"No existing model found, but new model rejected (MAE {new_mae:.2f} >= 2.3 limit).",
                )
                return False, "Model Rejected (Exceeds Absolute Limit)"

        details = f'{{"old_mae": {old_mae:.2f}, "new_mae": {new_mae:.2f}}}'

        # Accept new model if its MAE is better, equal, or up to 0.50 worse than the old model
        # AND it MUST be less than the absolute limit of 2.3
        if new_mae <= old_mae + 0.50 and new_mae < 2.3:
            if new_mae <= old_mae:
                log_msg = f"New Model is better or equal! (Old MAE: {old_mae:.2f}, New MAE: {new_mae:.2f})"
            else:
                log_msg = f"New Model accepted within 0.50 limit. (Old MAE: {old_mae:.2f}, New MAE: {new_mae:.2f})"

            log_event(db, "SUCCESS", component, log_msg, details)

            backup_filename = model_filename.replace(".json", "_backup.json")
            backup_path = os.path.join(model_dir, backup_filename)

            if os.path.exists(backup_path):
                os.remove(backup_path)

            if os.path.exists(model_path):
                os.rename(model_path, backup_path)

            new_model.save_model(model_path)
            log_event(
                db, "INFO", component, "Versioning complete. Old model is now backup."
            )
            ret = True, "Model Promoted"
        else:
            if new_mae >= 2.3:
                log_event(
                    db,
                    "WARNING",
                    component,
                    f"New Model rejected (Exceeded absolute 2.3 limit). (Old MAE: {old_mae:.2f}, New MAE: {new_mae:.2f})",
                    details,
                )
            else:
                log_event(
                    db,
                    "WARNING",
                    component,
                    f"New Model rejected (Exceeded 0.50 tolerance limit). (Old MAE: {old_mae:.2f}, New MAE: {new_mae:.2f})",
                    details,
                )
            ret = False, "Model Rejected"

    except Exception as e:
        db.rollback()
        log_event(db, "ERROR", component, f"Error during retraining: {str(e)}")
        ret = False, str(e)
    finally:
        db.close()

    return ret


def retrain_tft_pipeline(tft_dir):
    db = SessionLocal()
    component = "MLOps_TFT_3H"

    try:
        log_event(db, "INFO", component, "Started TFT Retraining Process")

        import subprocess
        import json

        script_path = os.path.join(tft_dir, "train_tft_model.py")
        subprocess.run([sys.executable, script_path], check=True, cwd=tft_dir)

        result_file = os.path.join(tft_dir, "tft_result.json")
        if os.path.exists(result_file):
            with open(result_file, "r") as f:
                res = json.load(f)
            best_model_path = res.get("best_model_path")
            best_val_loss = res.get("val_loss_val")
            try:
                os.remove(result_file)
            except Exception:
                pass
        else:
            best_model_path, best_val_loss = None, None

        if best_model_path:
            loss_str = (
                f"{best_val_loss:.2f}" if best_val_loss is not None else "Unknown"
            )
            msg = f"TFT Model trained successfully. MAE: {loss_str}"
            log_event(db, "SUCCESS", component, msg)
            ret = True, msg
        else:
            msg = "TFT Training completed but no checkpoint was saved."
            log_event(db, "WARNING", component, msg)
            ret = False, msg

        # --- Cleanup Old Lightning Logs ---
        # Keep only the 3 most recent versions to save space
        import shutil

        lightning_logs_dir = os.path.join(tft_dir, "lightning_logs")
        if os.path.exists(lightning_logs_dir):
            version_dirs = [
                d
                for d in os.listdir(lightning_logs_dir)
                if os.path.isdir(os.path.join(lightning_logs_dir, d))
                and d.startswith("version_")
            ]
            if len(version_dirs) > 3:
                version_dirs.sort(key=lambda x: int(x.split("_")[1]))
                dirs_to_delete = version_dirs[:-3]  # Keep the last 3
                for d in dirs_to_delete:
                    dir_path = os.path.join(lightning_logs_dir, d)
                    try:
                        shutil.rmtree(dir_path)
                        log_event(
                            db,
                            "INFO",
                            component,
                            f"Cleaned up old version to save space: {d}",
                        )
                    except Exception as e:
                        log_event(
                            db,
                            "WARNING",
                            component,
                            f"Failed to delete old version {d}: {e}",
                        )

    except Exception as e:
        db.rollback()
        log_event(db, "ERROR", component, f"Error during TFT retraining: {str(e)}")
        ret = False, str(e)
    finally:
        db.close()

    return ret


def run_wind_models_retraining():
    sync_training_data()
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../Models"))

    # 1st: 3H XGBoost Model
    dir_3h = os.path.join(base_dir, "wind_models/3h prediction model")
    res_3h, msg_3h = retrain_model_pipeline(
        3, "Wind speed(Kts)_3h_ahead", dir_3h, "xgboost_wind_model_3h.json"
    )

    # 2nd: TFT 3H Model
    dir_tft = os.path.join(base_dir, "wind_models/TFT_3H")
    res_tft, msg_tft = retrain_tft_pipeline(dir_tft)

    # 3rd: 1H XGBoost Model
    dir_1h = os.path.join(base_dir, "wind_models/1h prediction model")
    res_1h, msg_1h = retrain_model_pipeline(
        1, "Wind speed(Kts)_1h_ahead", dir_1h, "xgboost_wind_model_1h.json"
    )

    return {"3H_Wind_Model": msg_3h, "TFT_3H_Model": msg_tft, "1H_Wind_Model": msg_1h}


if __name__ == "__main__":
    results = run_wind_models_retraining()
    print("Retraining Results:", results)
