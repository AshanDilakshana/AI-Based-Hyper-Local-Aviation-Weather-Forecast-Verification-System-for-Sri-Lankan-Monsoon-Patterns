from fastapi import FastAPI
import sys
import os

# Ensure backend modules can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from backend.api.routers import mock_metrology
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

# ---------------------------------------------------------
# Include Route Modules (Different team members' models)
# ---------------------------------------------------------



# Mock Metrology API
app.include_router(mock_metrology.router)

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
        "active_models": ["QNH & Dewpoint Prediction"]
    }
