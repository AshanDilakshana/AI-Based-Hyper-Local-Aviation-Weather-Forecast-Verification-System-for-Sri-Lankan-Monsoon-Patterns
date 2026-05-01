from pydantic import BaseModel, Field
from typing import Optional

class WindPredictionRequest(BaseModel):
    temperature: float = Field(..., description="Current dry temperature in Celsius")
    dew_point: float = Field(..., description="Current dew point in Celsius")
    humidity: float = Field(..., description="Current relative humidity percentage")
    wind_dir: float = Field(..., description="Current wind direction in degrees (0-360)")
    past_wind_speed: float = Field(..., description="Wind speed from exactly 3 hours ago in knots")
    runway_heading: Optional[int] = Field(40, description="Runway heading. Default is Runway 04 (040 degrees)")

class WindPredictionResponse(BaseModel):
    predicted_wind_speed_kts: float
    headwind_kts: float
    crosswind_kts: float
    runway: str
    status: str
    message: str
