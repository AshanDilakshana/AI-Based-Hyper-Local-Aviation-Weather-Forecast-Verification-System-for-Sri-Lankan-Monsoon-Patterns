from fastapi import FastAPI, HTTPException
import sys
import os

# Ensure backend modules can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Import available local routers
from backend.api.routers import wind_router, temperature_pressure_router

# Safely import team routers (prevent crashes if they don't exist locally yet)
try:
    from backend.api.routers import live_metrology, forecast_router, logs_router, pilot_router
    has_team_routers = True
except ImportError:
    has_team_routers = False

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

# ---------------------------------------------------------
# Include Route Modules
# ---------------------------------------------------------

# Ashan's Wind Prediction Models
app.include_router(wind_router.router)

# Imash's Temperature & Pressure Prediction Models
app.include_router(temperature_pressure_router.router)

# Team's other routers (only included if available locally)
if has_team_routers:
    app.include_router(live_metrology.router)
    app.include_router(forecast_router.router)
    app.include_router(logs_router.router)
    app.include_router(pilot_router.router)

@app.get("/")
def read_root():
    return {
        "message": "Welcome to the Aviation Weather Forecast API.",
        "docs": "Visit /docs for the Swagger UI.",
        "active_models": ["Wind Prediction", "Temperature & Pressure"]
    }

# ---------------------------------------------------------
# Retrain Models
# ---------------------------------------------------------
try:
    from backend.mlops_retrainer import run_all_retrainings
except ImportError:
    # Fallback to your local retrainer if the main one isn't pulled yet
    def run_all_retrainings():
        from backend.mlops_retrainer_plugin import retrain_temperature_pressure_pipeline
        success, msg = retrain_temperature_pressure_pipeline()
        return {"Temperature_Pressure_Model": msg}

from backend.api.routers.wind_router import load_Wind_models
# Imash's model loader
from backend.api.routers.temperature_pressure_router import load_Temp_Press_models

@app.post("/models/retrain")
def manual_retrain_models():
    """
    Manually triggers the MLOps retraining pipeline.
    """
    try:
        results = run_all_retrainings()
        
        load_Wind_models() # Hot-reload models into memory
        
        # Load Temperature & Pressure models into memory!
        load_Temp_Press_models()
        
        return {"message": "Retraining complete", "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
