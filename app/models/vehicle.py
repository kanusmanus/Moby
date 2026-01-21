from typing import TYPE_CHECKING
from sqlalchemy import String, Integer, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.reservation import Reservation


class Vehicle(Base):
    __tablename__ = "vehicles"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    license_plate: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    make: Mapped[str] = mapped_column(String(50))
    model: Mapped[str] = mapped_column(String(50))
    color: Mapped[str] = mapped_column(String(30))
    year: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),  # let DB set it
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="vehicles")
    reservations: Mapped[list["Reservation"]] = relationship(
        back_populates="vehicle", passive_deletes=True
    )
