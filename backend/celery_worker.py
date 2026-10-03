import os
import sys
from celery import Celery

# Suppress TensorFlow logging and oneDNN warnings BEFORE any TF import occurs
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

from dotenv import load_dotenv

# Ensure backend modules can be imported
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))
sys.path.append(BASE_DIR)

# Configure Celery
# We use Redis as both the broker (message queue) and the backend (to store results)
REDIS_URL = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")

celery_app = Celery(
    "retrain_tasks",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

celery_app.conf.update(
    broker_connection_retry_on_startup=True,
    broker_transport_options={
        "visibility_timeout": 86400,
        "socket_timeout": 30.0,
        "socket_connect_timeout": 30.0,
    },
    result_backend_transport_options={
        "socket_timeout": 30.0,
        "socket_connect_timeout": 30.0,
    },
    redis_socket_timeout=30.0,
    redis_socket_connect_timeout=30.0,
    redis_backend_health_check_interval=20,
    broker_heartbeat=10,
    broker_pool_limit=10,
)



@celery_app.task(name="run_full_retraining_pipeline")
def run_full_retraining_pipeline():
    """
    Executes the MLOps retraining pipeline for all available models.
    This was moved from main.py so it can run asynchronously in the background.
    """
    results = {}

    # 1. Retrain core models (Wind)
    try:
        from backend.mlops_retrainer.mlops_Wind_retrainer import (
            run_wind_models_retraining,
        )

        results["Wind_Model"] = run_wind_models_retraining()
    except Exception as e:
        results["Wind_Model"] = f"Failed: {str(e)}"

    # 2. Imash's Temperature & Pressure Retraining
    try:
        from backend.mlops_retrainer.mlops_retrainer_temperature import (
            retrain_temperature_pressure,
        )

        success, msg, _ = retrain_temperature_pressure()
        results["Temperature_Pressure_Model"] = msg
    except ImportError:
        results["Temperature_Pressure_Model"] = "Skipped (not found)"
    except Exception as e:
        results["Temperature_Pressure_Model"] = f"Failed: {str(e)}"

    # 3. Sachiii - Cloud & Visibility Retraining
    try:
        from backend.mlops_retrainer.mlops_cloud_visibility_retrainer import (
            run_cloud_visibility_retraining,
        )

        success, msg = run_cloud_visibility_retraining()
        results["Cloud_Visibility_Model"] = msg
    except ImportError:
        results["Cloud_Visibility_Model"] = "Skipped (not found)"
    except Exception as e:
        results["Cloud_Visibility_Model"] = f"Failed: {str(e)}"

    # 4. viji's QNH/Dewpoint Retraining
    try:
        from backend.mlops_retrainer.mlops_qnh_dewpoint_retrainer import (
            run_qnh_dewpoint_retraining,
        )

        qnh_dew_res = run_qnh_dewpoint_retraining()
        results.update(qnh_dew_res)
    except Exception as e:
        results["QNH_Dewpoint_Model"] = f"Failed: {str(e)}"

    return results
