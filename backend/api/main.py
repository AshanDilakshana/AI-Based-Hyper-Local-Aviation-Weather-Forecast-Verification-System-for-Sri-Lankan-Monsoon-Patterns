import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "../.."))
BACKEND_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))
ROUTERS_DIR = os.path.join(BASE_DIR, "routers")

for path in [PROJECT_ROOT, BACKEND_DIR, BASE_DIR, ROUTERS_DIR]:
    if path not in sys.path:
        sys.path.insert(0, path)

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Import the Scheduler
try:
    from backend.scheduler import start_scheduler
except ImportError:
    pass

# Import routers safely
try:
    from backend.api.routers import cloud_visibility_router
except ImportError:
    try:
        from api.routers import cloud_visibility_router
    except ImportError:
        import cloud_visibility_router  # type: ignore[import-not-found]


app = FastAPI(
    title="Aviation Weather Forecast API",
    description="Main API gateway for multiple aviation weather models. (Cloud & Visibility Module)",
    version="1.0.0"
)

# Mount static directory for generated documents (Team standard)
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DOCS_DIR = os.path.join(DATA_DIR, "documents")
if not os.path.exists(DOCS_DIR):
    os.makedirs(DOCS_DIR, exist_ok=True)
app.mount("/documents", StaticFiles(directory=DOCS_DIR), name="documents")

@app.on_event("startup")
def on_startup():
    print("Starting background scheduler...")
    try:
        start_scheduler()
    except NameError:
        print("Scheduler not imported.")

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

# Sachiii / Ashan - Cloud & Visibility Prediction Models
app.include_router(cloud_visibility_router.router)

# Example placeholders for other team members to be merged:
# 
# try:
#     from backend.api.routers import wind_router
#     app.include_router(wind_router.router)
# except ImportError:
#     pass
#
# try:
#     from backend.api.routers import temperature_pressure_router
#     app.include_router(temperature_pressure_router.router)
# except ImportError:
#     pass


@app.get("/")
def read_root():
    return {
        "message": "Welcome to the Aviation Weather Forecast API.",
        "docs": "Visit /docs for the Swagger UI.",
        "active_models": ["Cloud Status", "Visibility"]
    }

# ---------------------------------------------------------
# MLOps Retraining Trigger
# ---------------------------------------------------------
from backend.mlops_retrainer.mlops_cloud_visibility_retrainer import run_cloud_visibility_retraining

@app.post("/models/retrain")
def manual_retrain_models():
    """
    Manually triggers the MLOps retraining pipeline.
    """
    try:
        # 1. Retrain core models (Cloud & Visibility)
        success, msg = run_cloud_visibility_retraining()
        results = {"Cloud_Visibility_Model": msg}
        
        # 2. Safely trigger other team members' retraining if available
        # try:
        #     from backend.mlops_retrainer.mlops_Wind_retrainer import run_wind_models_retraining
        #     results["Wind_Model"] = run_wind_models_retraining()
        # except ImportError:
        #     pass 
            
        # 3. Hot-reload models into memory (If supported by router)
        try:
            from backend.api.routers.cloud_visibility_router import load_models
            load_models()
        except ImportError:
            pass # Implement a load_models() function in your router for hot-reloading
            
        return {"message": "Retraining complete", "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.api.main:app", host="127.0.0.1", port=8000, reload=True)
