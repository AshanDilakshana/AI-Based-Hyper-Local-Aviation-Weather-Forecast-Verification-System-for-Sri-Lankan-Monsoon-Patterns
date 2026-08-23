from pydantic import BaseModel

class TempPressPredictionRequest(BaseModel):
    temperature: float
    humidity: float
    pressure: float
    dew_point: float
    wind_speed: float
    wind_direction: float
    visibility: float
