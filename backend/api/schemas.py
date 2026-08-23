from pydantic import BaseModel, Field
from typing import Optional

class TempPressPredictionRequest(BaseModel):
    temperature: float
    humidity: float
    pressure: float
    dew_point: float
    wind_speed: float
    wind_direction: float
    visibility: float

class WindPredictionRequest(BaseModel):
    temperature: float = Field(..., description="Current dry temperature in Celsius")
    dew_point: float = Field(..., description="Current dew point in Celsius")
    humidity: float = Field(..., description="Current relative humidity percentage")
    wind_dir: float = Field(..., description="Current wind direction in degrees (0-360)")
    runway_heading: int = Field(40, description="Runway heading for BIA (Default: 04 -> 40 degrees)")
    time_utc: Optional[str] = Field(None, description="Time in UTC (HHMM)")
    qnh_hpa: Optional[float] = Field(None, description="QNH in hPa - Required for 3H model")

class WindPredictionResponse(BaseModel):
    predicted_wind_speed_kts: float
    headwind_kts: float
    crosswind_kts: float
    runway: str
    status: str
    message: str
