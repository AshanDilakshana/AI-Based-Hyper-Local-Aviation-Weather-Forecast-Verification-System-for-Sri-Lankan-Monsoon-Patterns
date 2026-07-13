from fastapi import FastAPI
import sys
import os

# Ensure backend modules can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from backend.api.routers import weather_router, mock_metrology
from backend.data.database import engine, Base
from backend.data import models

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Aviation Weather Forecast API",
    description="Main API gateway for multiple aviation weather models.",
    version="1.0.0"
)

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(weather_router.router)
app.include_router(mock_metrology.router)

@app.get("/")
def read_root():
    return {
        "message": "Welcome to the Aviation Weather Forecast API (Temperature, Pressure, Humidity).",
        "docs": "Visit /docs for the Swagger UI.",
        "active_models": ["Weather Variables Prediction (T+3 Forecast)"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
