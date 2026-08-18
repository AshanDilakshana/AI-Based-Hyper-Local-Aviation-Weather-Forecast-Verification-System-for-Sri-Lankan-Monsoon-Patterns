from pydantic import BaseModel, Field  # type: ignore[import-not-found] # pyrefly: ignore [missing-import]



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

