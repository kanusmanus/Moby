from typing import TYPE_CHECKING
from sqlalchemy import String, Integer, Float, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.db.base import Base

if TYPE_CHECKING:
    from app.models.reservation import Reservation
    from app.models.parking_session import ParkingSession


class ParkingLot(Base):
    __tablename__ = "parking_lots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    location: Mapped[str] = mapped_column(String(120), nullable=False)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    reserved: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    tariff: Mapped[float] = mapped_column(Float, nullable=False)
    daytariff: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),  # let DB set it
    )
    created_by: Mapped[int] = mapped_column(Integer, nullable=False)

    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)

    reservations: Mapped[list["Reservation"]] = relationship(
        back_populates="parking_lot", passive_deletes=True
    )

    sessions: Mapped[list["ParkingSession"]] = relationship(
        back_populates="parking_lot", passive_deletes=True
    )
