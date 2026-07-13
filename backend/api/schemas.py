from pydantic import BaseModel, Field
from typing import Optional

class WeatherPredictionRequest(BaseModel):
    temperature: float = Field(..., description="Current dry temperature in Celsius")
    dew_point: float = Field(..., description="Current dew point in Celsius")
    humidity: float = Field(..., description="Current relative humidity percentage")
    wind_direction: float = Field(..., description="Current wind direction in degrees")
    wind_speed: float = Field(..., description="Current wind speed in Knots")
    pressure: float = Field(..., description="Current barometric pressure QNH in hPa")
    visibility: float = Field(..., description="Current visibility in meters")
    time_utc: Optional[str] = Field(None, description="Time in UTC (HHMM)")

class WeatherPredictionResponse(BaseModel):
    temperature: float
    pressure: float
    humidity: float
    forecast: str
    input_time_utc: str
    forecast_time_utc: str
