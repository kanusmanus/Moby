import enum
from typing import TYPE_CHECKING, Optional
from sqlalchemy import Enum, Float, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.reservation import Reservation
    from app.models.parking_session import ParkingSession


class PaymentStatus(str, enum.Enum):
    pending = "pending"
    paid = "paid"


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=True
    )
    reservation_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("reservations.id", ondelete="SET NULL"), index=True, nullable=True
    )

    session_id: Mapped[int] = mapped_column(
        ForeignKey("parking_sessions.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    amount: Mapped[float] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),  # let DB set it
    )

    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, name="payment_status"),
        nullable=False,
        default=PaymentStatus.pending,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    user: Mapped[Optional["User"]] = relationship(back_populates="payments")
    reservation: Mapped[Optional["Reservation"]] = relationship(
        back_populates="payment"
    )
    # Sessions with this payment
    session: Mapped["ParkingSession"] = relationship(
        back_populates="payment", uselist=False
    )
