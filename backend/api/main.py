from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Import our isolated components
from backend.api.routers import temperature_pressure_router
from backend.mlops_retrainer_plugin import retrain_temperature_pressure_pipeline

app = FastAPI(title="Local API Testing for Temp & Pressure")

# Configure CORS (mimicking typical setup)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. Include our Router
app.include_router(temperature_pressure_router.router)

# 2. Mimic the MLOps retrainer endpoint
@app.post("/models/retrain")
def manual_retrain_models():
    """
    Manually triggers the MLOps retraining pipeline for Temp/Pressure.
    This mimics how it will run in the friend's main app.
    """
    try:
        # Step 1: Run Retraining Plugin
        success, msg = retrain_temperature_pressure_pipeline()
        
        # Step 2: Hot-reload models into memory!
        temperature_pressure_router.load_Temp_Press_models()
        
        results = {
            "Temperature_Pressure_Model": msg
        }
        
        return {"message": "Retraining complete", "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def read_root():
    return {"message": "Local FastAPI Server is Running!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
