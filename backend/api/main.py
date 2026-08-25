
from fastapi import FastAPI, HTTPException
import os
import sys

# Suppress TensorFlow logging and oneDNN warnings BEFORE any TF import occurs
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# Ensure backend modules can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))



from backend.api.routers import live_metrology, forecast_router, logs_router, pilot_router
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
    lifespan=lifespan
)

# Mount static directory for generated documents
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DOCS_DIR = os.path.join(DATA_DIR, "documents")
if not os.path.exists(DOCS_DIR):
    os.makedirs(DOCS_DIR)
app.mount("/documents", StaticFiles(directory=DOCS_DIR), name="documents")


@app.on_event("startup")
def on_startup():
    print("Starting background scheduler...")
    # Call start_scheduler (which is non-blocking since it uses BackgroundScheduler)
    start_scheduler()

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
        "active_models": ["Temperature & Pressure", "Cloud Status", "Visibility", "QNH, Dewpoint & RH Prediction"]
    }


# ---------------------------------------------------------
# MLOps Retraining Endpoint
# ---------------------------------------------------------

from fastapi import HTTPException
from backend.mlops_retrainer.mlops_qnh_dewpoint_retrainer import run_qnh_dewpoint_retraining
from backend.api.routers.qnh_dewpoint_router import load_QNH_Dewpoint_models

@app.post("/models/retrain")
def manual_retrain_models():
    """
    Manually triggers the MLOps retraining pipeline for all available models.
    """
    try:
        results = {}
        
        # 1. Retrain core models (Wind)
        try:
            from backend.mlops_retrainer.mlops_Wind_retrainer import run_wind_models_retraining
            from backend.api.routers.wind_router import load_Wind_models
            results["Wind_Model"] = run_wind_models_retraining()
            load_Wind_models() 
        except Exception as e:
            results["Wind_Model"] = f"Failed: {str(e)}"
            
        # 2. Imash's Temperature & Pressure Retraining (ACTIVE)
        try:
            from backend.mlops_retrainer.mlops_retrainer_temperature import retrain_temperature_pressure
            success, msg, _ = retrain_temperature_pressure()
            results["Temperature_Pressure_Model"] = msg
        except ImportError:
            results["Temperature_Pressure_Model"] = "Skipped (not found)"

        # Hot-reload Temperature & Pressure models into memory
        try:
            from backend.api.routers.temperature_pressure_router import load_Temp_Press_models
            load_Temp_Press_models()
        except Exception as e:
            results["Temperature_Pressure_Reload"] = f"Failed to reload: {str(e)}"

        # 3. Sachiii - Cloud & Visibility Retraining (ACTIVE)
        try:
            from backend.mlops_retrainer.mlops_cloud_visibility_retrainer import run_cloud_visibility_retraining
            success, msg = run_cloud_visibility_retraining()
            results["Cloud_Visibility_Model"] = msg
        except ImportError:
            results["Cloud_Visibility_Model"] = "Skipped (not found)"

        # Hot-reload Cloud & Visibility models into memory
        try:
            from backend.api.routers.cloud_visibility_router import load_models
            load_models()
        except Exception as e:
            results["Cloud_Visibility_Reload"] = f"Failed to reload: {str(e)}"

        # 4.viji's QNH/Dewpoint Retraining
        try:
            qnh_dew_res = run_qnh_dewpoint_retraining()
            results.update(qnh_dew_res)
        except Exception as e:
            results["QNH_Dewpoint_Model"] = f"Failed: {str(e)}"
            
        # Hot-reload QNH & Dewpoint models into memory
        try:
            load_QNH_Dewpoint_models()
        except Exception as e:
            results["QNH_Dewpoint_Reload"] = f"Failed to reload: {str(e)}"

        return {"message": "Retraining complete", "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
