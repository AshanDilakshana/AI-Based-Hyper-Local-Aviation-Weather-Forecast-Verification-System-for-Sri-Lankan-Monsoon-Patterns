from fastapi import FastAPI
import sys
import os

# Ensure backend modules can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from backend.api.routers import wind_router, live_metrology, forecast_router, logs_router, pilot_router
from backend.data.database import engine, Base
from backend.data import models

# Create database tables
Base.metadata.create_all(bind=engine)

from backend.scheduler import start_scheduler

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

# Live Metrology API
app.include_router(live_metrology.router)

# Verified Forecasts API
app.include_router(forecast_router.router)

# System & Activity Logs API
app.include_router(logs_router.router)

# Pilot Flight Planning & Document API
app.include_router(pilot_router.router)


# Ashan's Wind Prediction Models (1h & 3h)
app.include_router(wind_router.router)


# Example placeholders for other team members:
# (Safely imported so that missing files locally don't crash the main server)

# Imash - Temperature & Pressure
# try:
#     from backend.api.routers import temperature_pressure_router
#     app.include_router(temperature_pressure_router.router)
# except ImportError:
#     print("Warning: temperature_pressure_router not found locally. Skipping.")

# Sachiii - Visibility (Placeholder)
# try:
#     from backend.api.routers import visibility_router
#     app.include_router(visibility_router.router)
# except ImportError:
#     pass # Ignored until visibility_router is merged

# Vijjj - Clouds (Placeholder)
# try:
#     from backend.api.routers import clouds_router
#     app.include_router(clouds_router.router)
# except ImportError:
#     pass # Ignored until clouds_router is merged

@app.get("/")
def read_root():
    return {
        "message": "Welcome to the Aviation Weather Forecast API.",
        "docs": "Visit /docs for the Swagger UI.",
        "active_models": ["Wind Prediction"]
    }



#retrain models from api request

from fastapi import HTTPException
from backend.mlops_retrainer.mlops_Wind_retrainer import run_wind_models_retraining
from backend.api.routers.wind_router import load_Wind_models
# ---------------------------------------------------------
# (imash,sachiii,vijjj): Import your model loading functions here!
# ---------------------------------------------------------
# try:
#     from backend.api.routers.temperature_pressure_router import load_Temp_Press_models
#     from backend.mlops_retrainer_plugin import retrain_temperature_pressure_pipeline
# except ImportError:
#     pass

# try:
#     from backend.api.routers.visibility_router import load_Visibility_models
# except ImportError:
#     pass

# try:
#     from backend.api.routers.clouds_router import load_Clouds_models
# except ImportError:
#     pass
# ---------------------------------------------------------

@app.post("/models/retrain")
def manual_retrain_models():
    """
    Manually triggers the MLOps retraining pipeline.
    """
    try:
        # 1. Retrain core models (Wind)
        results = run_wind_models_retraining()
        
        # 2. Safely trigger other team members' retraining if available
        # try:
        #     temp_success, temp_msg = retrain_temperature_pressure_pipeline()
        #     results["Temperature_Pressure_Model"] = temp_msg
        # except NameError:
        #     pass # retrain_temperature_pressure_pipeline not imported
            
        # 3. Hot-reload models into memory
        load_Wind_models() 
        
        # ---------------------------------------------------------
        # (imash,sachiii,vijjj): Call your model loading functions here 
        # so they update in RAM after retraining!
        # ---------------------------------------------------------
        # try:
        #     load_Temp_Press_models()
        # except NameError:
        #     pass
            
        # try:
        #     load_Visibility_models()
        # except NameError:
        #     pass
            
        # try:
        #     load_Clouds_models()
        # except NameError:
        #     pass
        
        return {"message": "Retraining complete", "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))