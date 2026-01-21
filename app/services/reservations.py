from typing import Optional
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.models.reservation import Reservation, ReservationStatus, ReservationChannel
from app.models.parking_lot import ParkingLot
from app.models.user import User
from app.schemas.reservations import ReservationIn
from app.services.exceptions import (
    ParkingLotNotFound,
    ParkingLotAtCapacity,
    ReservationNotFound,
)
from app.services.discounts import apply_discount, record_discount_redemption


async def check_capacity(
    db: AsyncSession,
    parking_lot_id: int,
    planned_start: datetime,
    planned_end: datetime,
    exclude_reservation_id: Optional[int] = None,
) -> bool:
    """Check if parking lot has capacity for a new reservation."""

    # Get parking lot
    lot = await db.get(ParkingLot, parking_lot_id)
    if not lot:
        raise ParkingLotNotFound()

    # Count overlapping confirmed/pending reservations
    query = select(func.count(Reservation.id)).where(
        and_(
            Reservation.parking_lot_id == parking_lot_id,
            Reservation.status.in_(
                [ReservationStatus.confirmed, ReservationStatus.pending]
            ),
            # Time overlap: new reservation overlaps if:
            # new_start < existing_end AND new_end > existing_start
            Reservation.planned_end > planned_start,
            Reservation.planned_start < planned_end,
        )
    )

    if exclude_reservation_id:
        query = query.where(Reservation.id != exclude_reservation_id)

    result = await db.execute(query)
    overlapping_count = result.scalar()

    if overlapping_count is None:
        overlapping_count = 0

    # Check if we have capacity
    return overlapping_count < lot.capacity


async def calculate_reservation_cost(
    db: AsyncSession,
    parking_lot_id: int,
    planned_start: datetime,
    planned_end: datetime,
) -> float:
    """Calculate cost for a reservation."""
    lot = await db.get(ParkingLot, parking_lot_id)
    if not lot:
        raise ParkingLotNotFound()

    duration_hours = (planned_end - planned_start).total_seconds() / 3600

    # Use hourly tariff
    return duration_hours * lot.tariff


async def create_reservation(
    db: AsyncSession, payload: ReservationIn, current_user: User
) -> Reservation:
    """Create a new reservation with capacity checking."""

    # 1. Check capacity
    has_capacity = await check_capacity(
        db, payload.parking_lot_id, payload.planned_start, payload.planned_end
    )

    if not has_capacity:
        raise ParkingLotAtCapacity()

    # 2. Calculate cost
    original_cost = await calculate_reservation_cost(
        db, payload.parking_lot_id, payload.planned_start, payload.planned_end
    )

    # 3. Apply discount if provided
    final_cost, discount_amount, discount_code_id, dc = await apply_discount(
        db, original_cost, payload.discount_code
    )

    # 4. Create reservation
    reservation = Reservation(
        user_id=current_user.id,
        parking_lot_id=payload.parking_lot_id,
        vehicle_id=payload.vehicle_id,
        license_plate=payload.license_plate,
        planned_start=payload.planned_start,
        planned_end=payload.planned_end,
        channel=ReservationChannel.registered,
        status=ReservationStatus.confirmed,
        quoted_cost=final_cost,
        original_cost=original_cost,
        discount_amount=discount_amount,
        discount_code_id=discount_code_id,
    )

    db.add(reservation)

    # 5. Record discount redemption if used
    if discount_code_id and dc:
        await record_discount_redemption(db, dc, current_user.id, reservation)

    await db.flush()
    await db.commit()
    await db.refresh(reservation)

    return reservation


async def retrieve_reservation(
    db: AsyncSession, reservation_id: int, current_user: User
) -> Reservation:
    """Get a reservation by ID."""
    reservation = await db.get(Reservation, reservation_id)

    if not reservation:
        raise ReservationNotFound()

    # Check authorization (user can only see their own unless admin)
    if current_user.role != "admin" and reservation.user_id != current_user.id:
        from fastapi import HTTPException

        raise HTTPException(status_code=403, detail="Not authorized")

    return reservation


async def try_get_valid_reservation_by_plate(
    db: AsyncSession, parking_lot_id: int, license_plate: str, current_time: datetime
) -> Optional[Reservation]:
    """Get valid reservation for a license plate at current time."""
    result = await db.execute(
        select(Reservation).where(
            and_(
                Reservation.parking_lot_id == parking_lot_id,
                Reservation.license_plate == license_plate,
                Reservation.status == ReservationStatus.confirmed,
                Reservation.planned_start <= current_time,
                Reservation.planned_end >= current_time,
            )
        )
    )
    return result.scalar_one_or_none()

