from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict
from datetime import datetime


# Mirror SQLA Enum so input can be validated
class SessionStatus(str, Enum):
    active = "active"
    closed = "closed"
    void = "void"
    violation = "violation"


class ParkingSessionIn(BaseModel):
    parking_lot_id: int
    reservation_id: Optional[int] = None
    vehicle_id: Optional[int] = None
    license_plate: str
    entry_time: datetime
    entry_gate_id: int


class ParkingSessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    parking_lot_id: int
    reservation_id: Optional[int] = None
    vehicle_id: Optional[int] = None
    license_plate: str
    entry_time: datetime
    entry_gate_id: int
    status: SessionStatus
