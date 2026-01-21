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
import enum

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.vehicle import Vehicle
    from app.models.parking_lot import ParkingLot
    from app.models.discount_code import DiscountCode
    from app.models.parking_session import ParkingSession
    from app.models.payment import Payment


class ReservationChannel(str, enum.Enum):
    registered = "registered"
    anonymous_driveup = "anonymous_driveup"
    company = "company"
    hotel = "hotel"


class ReservationStatus(str, enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    cancelled = "cancelled"
    expired = "expired"
    completed = "completed"


class Reservation(Base, TimestampMixin):
    __tablename__ = "reservations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    parking_lot_id: Mapped[int] = mapped_column(
        ForeignKey("parking_lots.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    # Registered context (nullable for anonymous)
    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )

    vehicle_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("vehicles.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )

    license_plate: Mapped[str] = mapped_column(String(16), index=True, nullable=False)

    planned_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    planned_end: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    channel: Mapped[ReservationChannel] = mapped_column(
        Enum(ReservationChannel, name="reservation_channel"),
        nullable=False,
        default=ReservationChannel.registered,
    )

    status: Mapped[ReservationStatus] = mapped_column(
        Enum(ReservationStatus, name="reservation_status"),
        nullable=False,
        default=ReservationStatus.confirmed,
    )

    # Expected/quoted cost (final belongs on session/payment)
    quoted_cost: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    __table_args__ = (
        # Basic sanity
        CheckConstraint(
            "planned_end > planned_start", name="ck_reservation_time_order"
        ),
        # Enforce consistent identity rules:
        # - registered: must have user_id and vehicle_id
        # - anonymous_driveup: must have license_plate and must NOT have user_id/vehicle_id
        CheckConstraint(
            """
            (
              channel = 'registered' AND user_id IS NOT NULL AND vehicle_id IS NOT NULL
            )
            OR
            (
              channel = 'anonymous_driveup' AND user_id IS NULL AND vehicle_id IS NULL AND license_plate IS NOT NULL
            )
            OR
            (
              channel IN ('company','hotel')
            )
            """,
            name="ck_reservation_channel_identity",
        ),
        Index(
            "ix_reservation_lot_time", "parking_lot_id", "planned_start", "planned_end"
        ),
    )

    discount_code_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("discount_codes.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )

    original_cost: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    discount_amount: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # --- Relationships ---
    user: Mapped[Optional["User"]] = relationship(
        back_populates="reservations", passive_deletes=True
    )
    vehicle: Mapped[Optional["Vehicle"]] = relationship(
        back_populates="reservations", passive_deletes=True
    )
    parking_lot: Mapped["ParkingLot"] = relationship(
        back_populates="reservations", passive_deletes=True
    )

    # If you keep a 1:1 payment per reservation you can keep this,
    # but for drive-up it often belongs to session.
    payment: Mapped[Optional["Payment"]] = relationship(
        back_populates="reservation", uselist=False
    )
    discount_code: Mapped[Optional["DiscountCode"]] = relationship(
        "DiscountCode", passive_deletes=True
    )

    # Sessions created from this reservation (often 0..1, but allow 1..n to be safe)
    sessions: Mapped[list["ParkingSession"]] = relationship(
        back_populates="reservation"
    )
