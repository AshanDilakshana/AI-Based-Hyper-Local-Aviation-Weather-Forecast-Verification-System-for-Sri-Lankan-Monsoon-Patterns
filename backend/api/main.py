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

from backend.data.database import engine, Base
from backend.data import models

# Create database tables
Base.metadata.create_all(bind=engine)

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


# Placeholders for other team members' routers (Visibility, Clouds, etc.)
try:
    from backend.api.routers import visibility_router
    app.include_router(visibility_router.router)
except ImportError:
    pass

try:
    from backend.api.routers import clouds_router
    app.include_router(clouds_router.router)
except ImportError:
    pass

@app.get("/")
def read_root():
    return {
        "message": "Welcome to the Aviation Weather Forecast API.",
        "docs": "Visit /docs for the Swagger UI.",
        "active_models": ["Temperature & Pressure"]
    }

# ---------------------------------------------------------
# MLOps Retraining Endpoint
# ---------------------------------------------------------
@app.post("/models/retrain")
def manual_retrain_models():
    """
    Manually triggers the MLOps retraining pipeline for all available models.
    """
    results = {}
    try:
        # Imash's Temperature & Pressure Retraining (ACTIVE)
        try:
            from backend.mlops_retrainer import retrain_temperature_pressure_pipeline
            success, msg = retrain_temperature_pressure_pipeline()
            results["Temperature_Pressure_Model"] = msg
        except ImportError:
            results["Temperature_Pressure_Model"] = "Skipped (not found)"

        # Hot-reload models into memory
        try:
            from backend.api.routers.temperature_pressure_router import load_Temp_Press_models
            load_Temp_Press_models()
        except ImportError:
            pass

        return {"message": "Retraining complete", "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
