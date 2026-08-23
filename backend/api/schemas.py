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

class CloudVisibilityRequest(BaseModel):
    temp: float = Field(..., description="Dry Temperature in Celsius")
    dew: float = Field(..., description="Dew Point in Celsius")
    rh: float = Field(..., description="Relative Humidity percentage")
    qnh: float = Field(..., description="QNH Pressure in hPa")
    wind: float = Field(..., description="Wind Speed in Knots")
    month: float | None = Field(default=6.0, description="Month of the year (1-12)")
    hour: float | None = Field(default=12.0, description="Hour of the day in UTC (0-23)")
    wind_dir: float | None = Field(default=180.0, description="Wind direction in degrees")
    weather_encoded: float | None = Field(default=0.0, description="Encoded weather condition index")


class CloudVisibilityResponse(BaseModel):
    visibility_prediction: int = Field(..., description="Predicted visibility in meters")
    cloud_status: str = Field(..., description="Predicted cloud status/coverage string")
