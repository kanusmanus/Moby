from enum import Enum
from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class GateDirection(str, Enum):
    entry = "entry"
    exit = "exit"


class GateEventIn(BaseModel):
    gate_id: int
    parking_lot_id: int
    license_plate: str
    direction: GateDirection
    timestamp: datetime


class GateDecision(str, Enum):
    open = "open"
    deny = "deny"


class GateEventOut(BaseModel):
    gate_id: int
    decision: GateDecision
    reason: Optional[str] = None

    session_id: Optional[int] = None
    reservation_id: Optional[int] = None


class GateIn(BaseModel):
    parking_lot_id: int


class GateOut(BaseModel):
    id: int
    parking_lot_id: int
