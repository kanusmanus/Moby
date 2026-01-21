from datetime import datetime
from enum import Enum
from pydantic import BaseModel, ConfigDict


# Mirror SQLA Enum so input can be validated
class PaymentStatus(str, Enum):
    pending = "pending"
    paid = "paid"


class PaymentIn(BaseModel):
    parking_lot_id: int
    license_plate: str


class PaymentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    amount: float
    completed_at: datetime
    status: PaymentStatus
