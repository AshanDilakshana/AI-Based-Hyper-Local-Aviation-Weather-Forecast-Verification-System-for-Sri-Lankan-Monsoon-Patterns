from fastapi import FastAPI, HTTPException
import sys
import os

# Ensure backend modules can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Import available local routers
from backend.api.routers import temperature_pressure_router

from backend.data.database import engine, Base
from backend.data import models

# Create database tables
Base.metadata.create_all(bind=engine)

try:
    from backend.scheduler import start_scheduler
except ImportError:
    def start_scheduler():
        print("Scheduler not found locally.")

from fastapi.staticfiles import StaticFiles

app = FastAPI(
    title="Aviation Weather Forecast API",
    description="Main API gateway for multiple aviation weather models.",
    version="1.0.0"
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
    start_scheduler()

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Route Modules
# ---------------------------------------------------------

try:
    app.include_router(temperature_pressure_router.router)
except NameError:
    print("Warning: temperature_pressure_router not found locally. Skipping.")

try:
    from backend.api.routers import dashboard_router
    app.include_router(dashboard_router.router)
except ImportError:
    print("Warning: dashboard_router not found locally. Skipping.")

@app.get("/")
def read_root():
    return {
        "message": "Welcome to the Aviation Weather Forecast API.",
        "docs": "Visit /docs for the Swagger UI.",
        "active_models": ["Temperature & Pressure"]
    }

# ---------------------------------------------------------
# Retrain Models
# ---------------------------------------------------------
try:
    from backend.mlops_retrainer import run_all_retrainings
except ImportError:
    # Fallback to your local retrainer if the main one isn't pulled yet
    def run_all_retrainings():
        from backend.mlops_retrainer import retrain_temperature_pressure_pipeline
        success, msg = retrain_temperature_pressure_pipeline()
        return {"Temperature_Pressure_Model": msg}

# Imash's model loader
try:
    from backend.api.routers.temperature_pressure_router import load_Temp_Press_models
except ImportError:
    pass

@app.post("/models/retrain")
def manual_retrain_models():
    """
    Manually triggers the MLOps retraining pipeline.
    """
    try:
        results = run_all_retrainings()
        
        # Load Temperature & Pressure models into memory!
        try:
            load_Temp_Press_models()
        except NameError:
            pass
        
        return {"message": "Retraining complete", "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
