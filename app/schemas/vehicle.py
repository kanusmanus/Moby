from pydantic import BaseModel, ConfigDict
from datetime import datetime


class VehicleIn(BaseModel):
    license_plate: str
    make: str
    model: str
    color: str
    year: int


class VehicleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    license_plate: str
    make: str
    model: str
    color: str
    year: int
    created_at: datetime
