import enum
from typing import TYPE_CHECKING, Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Enum,
    DateTime,
    Index,
    Integer,
    Float,
    String,
)
from datetime import datetime
from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.parking_lot import ParkingLot
    from app.models.reservation import Reservation
    from app.models.payment import Payment


class SessionStatus(str, enum.Enum):
    active = "active"
    closed = "closed"
    void = "void"
    violation = "violation"


class ParkingSession(Base, TimestampMixin):
    __tablename__ = "parking_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    parking_lot_id: Mapped[int] = mapped_column(
        ForeignKey("parking_lots.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    reservation_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("reservations.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )

    license_plate: Mapped[str] = mapped_column(String(16), index=True, nullable=False)

    entry_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    exit_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    entry_gate_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("gates.id", ondelete="SET NULL"), nullable=True
    )
    exit_gate_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("gates.id", ondelete="SET NULL"), nullable=True
    )

    status: Mapped[SessionStatus] = mapped_column(
        Enum(SessionStatus, name="session_status"),
        nullable=False,
        default=SessionStatus.active,
    )

    # Billing truth
    amount_due: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    amount_paid: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    closed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        CheckConstraint(
            "exit_time IS NULL OR exit_time >= entry_time", name="ck_session_time_order"
        ),
        Index("ix_session_lot_entry", "parking_lot_id", "entry_time"),
        Index("ix_session_plate_active_lookup", "license_plate", "status"),
    )

    # --- Relationships ---
    reservation: Mapped[Optional["Reservation"]] = relationship(
        back_populates="sessions"
    )
    parking_lot: Mapped["ParkingLot"] = relationship(back_populates="sessions")

    payment: Mapped["Payment"] = relationship(
        back_populates="session",
        uselist=False,
        cascade="all, delete-orphan",
        single_parent=True,
    )
