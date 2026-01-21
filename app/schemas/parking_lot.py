from pydantic import BaseModel, ConfigDict
from datetime import datetime


class ParkingLotIn(BaseModel):
    name: str
    location: str
    address: str
    capacity: int
    created_by: int
    reserved: int
    tariff: float
    daytariff: float
    latitude: float
    longitude: float


class ParkingLotOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    location: str
    address: str
    capacity: int
    created_by: int
    reserved: int
    tariff: float
    daytariff: float
    latitude: float
    longitude: float
    created_at: datetime


class ParkingLotCostIn(BaseModel):
    id: int
    hours: int
