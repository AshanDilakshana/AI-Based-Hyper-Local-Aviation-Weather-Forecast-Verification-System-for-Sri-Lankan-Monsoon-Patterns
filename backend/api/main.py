import os
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Suppress TensorFlow logging and oneDNN warnings BEFORE any TF import occurs
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# Ensure backend modules can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))


from backend.api.routers import (
    live_metrology,
    forecast_router,
    logs_router,
    pilot_router,
    auth_router,
)
from backend.data.database import engine, Base
from backend.data import models

# Create database tables
Base.metadata.create_all(bind=engine)

from fastapi.staticfiles import StaticFiles

try:
    from backend.scheduler import start_scheduler
except ImportError:

    def start_scheduler():
        print("Scheduler not found locally.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting background scheduler...")
    start_scheduler()
    yield


app = FastAPI(
    title="Aviation Weather Forecast API",
    description="Main API gateway for aviation weather models.",
    version="1.0.0",
    lifespan=lifespan,
)

# Mount static directory for generated documents
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DOCS_DIR = os.path.join(DATA_DIR, "documents")
if not os.path.exists(DOCS_DIR):
    os.makedirs(DOCS_DIR)
app.mount("/documents", StaticFiles(directory=DOCS_DIR), name="documents")


from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------
# Include Route Modules
# ---------------------------------------------------------

# Live Metrology API
app.include_router(live_metrology.router)

# Verified Forecasts API
app.include_router(forecast_router.router)

# System & Activity Logs API
app.include_router(logs_router.router)

# Pilot Flight Planning & Document API
app.include_router(pilot_router.router)

# Auth API
app.include_router(auth_router.router)


# Mock Metrology API (Local placeholder)


# (Safely imported so that missing files locally don't crash the main server)

# Ashan's Wind Prediction Models (ACTIVE)
try:
    from backend.api.routers import wind_router

    app.include_router(wind_router.router)
except ImportError:
    print("Warning: wind_router not found locally. Skipping.")


# Imash - Temperature & Pressure (ACTIVE)
try:
    from backend.api.routers import temperature_pressure_router

    app.include_router(temperature_pressure_router.router)
except ImportError:
    print("Warning: temperature_pressure_router not found locally. Skipping.")

# Dashboard Router
try:
    from backend.api.routers import dashboard_router

    app.include_router(dashboard_router.router)
except ImportError:
    print("Warning: dashboard_router not found locally. Skipping.")


# Sachiii - Cloud & Visibility Prediction Models (ACTIVE)
try:
    from backend.api.routers import cloud_visibility_router

    app.include_router(cloud_visibility_router.router)
except ImportError:
    print("Warning: cloud_visibility_router not found locally. Skipping.")


# viji - QNH, Dewpoint & RH Models (ACTIVE)
try:
    from backend.api.routers import qnh_dewpoint_router

    app.include_router(qnh_dewpoint_router.router)
except ImportError:
    print("Warning: qnh_dewpoint_router not found locally. Skipping.")


@app.get("/")
def read_root():
    return {
        "message": "Welcome to the Aviation Weather Forecast API.",
        "docs": "Visit /docs for the Swagger UI.",
        "active_models": [
            "Temperature & Pressure",
            "Cloud Status",
            "Visibility",
            "QNH, Dewpoint & RH Prediction",
        ],
    }


# ---------------------------------------------------------
# MLOps Retraining Endpoint
# ---------------------------------------------------------

from fastapi import HTTPException
from backend.mlops_retrainer.mlops_qnh_dewpoint_retrainer import (
    run_qnh_dewpoint_retraining,
)
from backend.api.routers.qnh_dewpoint_router import load_QNH_Dewpoint_models

from backend.celery_worker import run_full_retraining_pipeline, celery_app


@app.post("/models/retrain")
def manual_retrain_models():
    """
    Triggers the MLOps retraining pipeline in the background using Celery.
    """
    try:
        task = run_full_retraining_pipeline.delay()
        return {"message": "Retraining started in background", "task_id": task.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/models/retrain/status/{task_id}")
def get_retrain_status(task_id: str):
    """
    Check the status of a background retraining task.
    """
    task_result = celery_app.AsyncResult(task_id)

    # If the task is finished and successful, hot-reload the models into memory
    if task_result.status == "SUCCESS":
        try:
            try:
                from backend.api.routers.wind_router import load_Wind_models

                load_Wind_models()
            except ImportError:
                pass

            try:
                from backend.api.routers.temperature_pressure_router import (
                    load_Temp_Press_models,
                )

                load_Temp_Press_models()
            except ImportError:
                pass

            try:
                from backend.api.routers.cloud_visibility_router import (
                    load_models as load_Cloud_models,
                )

                load_Cloud_models()
            except ImportError:
                pass

            try:
                from backend.api.routers.qnh_dewpoint_router import (
                    load_QNH_Dewpoint_models,
                )

                load_QNH_Dewpoint_models()
            except ImportError:
                pass

        except Exception as e:
            print(f"Warning: Failed to hot-reload some models after retraining: {e}")

    return {
        "task_id": task_id,
        "status": task_result.status,
        "result": task_result.result if task_result.status == "SUCCESS" else None,
        "error": str(task_result.info) if task_result.status == "FAILURE" else None,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
