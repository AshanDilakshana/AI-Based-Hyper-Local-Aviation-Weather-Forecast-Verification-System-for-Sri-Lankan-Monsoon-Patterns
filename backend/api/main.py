from fastapi import FastAPI, HTTPException
import sys
import os

# Ensure backend modules can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from backend.api.routers import mock_metrology, qnh_dewpoint_router
from backend.data.database import engine, Base
from backend.data import models

# Create database tables
Base.metadata.create_all(bind=engine)

try:
    from backend.scheduler import start_scheduler
except ImportError:
    pass

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
    try:
        start_scheduler()
    except NameError:
        pass

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

# Ashan - QNH, Dewpoint & RH Models
app.include_router(qnh_dewpoint_router.router)

# Mock Metrology API (Local placeholder)
app.include_router(mock_metrology.router)


# Example placeholders for other team members:
# (Safely imported so that missing files locally don't crash the main server)

# Imash - Temperature & Pressure
# try:
#     from backend.api.routers import temperature_pressure_router
#     app.include_router(temperature_pressure_router.router)
# except ImportError:
#     pass

# Sachiii - Visibility (Placeholder)
# try:
#     from backend.api.routers import visibility_router
#     app.include_router(visibility_router.router)
# except ImportError:
#     pass

# Vijjj - Clouds (Placeholder)
# try:
#     from backend.api.routers import clouds_router
#     app.include_router(clouds_router.router)
# except ImportError:
#     pass

@app.get("/")
def read_root():
    return {
        "message": "Welcome to the Aviation Weather Forecast API.",
        "docs": "Visit /docs for the Swagger UI.",
        "active_models": ["QNH, Dewpoint & RH Prediction"]
    }

# ---------------------------------------------------------
# Retrain models from API request
# ---------------------------------------------------------

from backend.mlops_retrainer.mlops_qnh_dewpoint_retrainer import run_qnh_dewpoint_retraining
from backend.api.routers.qnh_dewpoint_router import load_QNH_Dewpoint_models

@app.post("/models/retrain")
def manual_retrain_models():
    """
    Manually triggers the MLOps retraining pipeline.
    """
    try:
        results = {}
        
        # 1. Ashan's QNH/Dewpoint Retraining
        try:
            qnh_dew_res = run_qnh_dewpoint_retraining()
            results.update(qnh_dew_res)
        except Exception as e:
            results["QNH_Dewpoint_Model"] = f"Failed: {str(e)}"
            
        # 2. Hot-reload models into memory
        load_QNH_Dewpoint_models()
        
        return {"message": "Retraining complete", "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
