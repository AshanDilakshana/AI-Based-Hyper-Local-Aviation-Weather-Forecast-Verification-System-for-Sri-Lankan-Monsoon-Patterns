from fastapi import FastAPI
import sys
import os

# Ensure backend modules can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from backend.api.routers import wind_router, live_metrology, forecast_router
from backend.data.database import engine, Base
from backend.data import models

# Create database tables
Base.metadata.create_all(bind=engine)

from backend.scheduler import start_scheduler

app = FastAPI(
    title="Aviation Weather Forecast API",
    description="Main API gateway for multiple aviation weather models.",
    version="1.0.0"
)

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
# Include Route Modules (Different team members' models)
# ---------------------------------------------------------

# Ashan's Wind Prediction Models (1h & 3h)
app.include_router(wind_router.router)

# Live Metrology API
app.include_router(live_metrology.router)

# Verified Forecasts API
app.include_router(forecast_router.router)

# Example placeholders for other team members:
# from backend.api.routers import visibility, clouds, temperature
# app.include_router(visibility.router)
# app.include_router(clouds.router)
# app.include_router(temperature.router)

@app.get("/")
def read_root():
    return {
        "message": "Welcome to the Aviation Weather Forecast API.",
        "docs": "Visit /docs for the Swagger UI.",
        "active_models": ["Wind Prediction"]
    }



#retrain models from api request

from fastapi import HTTPException
from backend.mlops_retrainer import run_all_retrainings
from backend.api.routers.wind_router import load_Wind_models
# ---------------------------------------------------------
# (imash,sachiii,vijjj): Import your model loading functions here!
# Example:
# from backend.api.routers.visibility_router import load_Visibility_models
# from backend.api.routers.clouds_router import load_Clouds_models
# ---------------------------------------------------------

@app.post("/models/retrain")
def manual_retrain_models():
    """
    Manually triggers the MLOps retraining pipeline.
    """
    try:
        results = run_all_retrainings()
        
        load_Wind_models() # Hot-reload models into memory
        # ---------------------------------------------------------
        # (imash,sachiii,vijjj): Call your model loading functions here 
        # so they update in RAM after retraining!
        # Example:
        # load_Visibility_models()
        # load_Clouds_models()
        # ---------------------------------------------------------
        
        return {"message": "Retraining complete", "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))