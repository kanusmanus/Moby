from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, Integer, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.db.base import Base

if TYPE_CHECKING:
    from app.models.parking_lot import ParkingLot


class Gate(Base):
    __tablename__ = "gates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),  # let DB set it
    )
    parking_lot_id: Mapped[int] = mapped_column(
        ForeignKey("parking_lots.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    parking_lot: Mapped["ParkingLot"] = relationship()
