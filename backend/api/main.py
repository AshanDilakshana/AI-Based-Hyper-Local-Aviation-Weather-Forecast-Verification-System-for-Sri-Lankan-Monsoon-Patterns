from fastapi import FastAPI
import sys
import os

# Ensure backend modules can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from backend.api.routers import wind

app = FastAPI(
    title="Aviation Weather Forecast API",
    description="Main API gateway for multiple aviation weather models.",
    version="1.0.0"
)

# ---------------------------------------------------------
# Include Route Modules (Different team members' models)
# ---------------------------------------------------------

# Ashan's Wind Prediction Model
app.include_router(wind.router)

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
