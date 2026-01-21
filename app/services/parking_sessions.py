from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.parking_session import ParkingSession, SessionStatus
from app.models.payment import Payment, PaymentStatus
from app.models.reservation import Reservation
from app.schemas.gate import GateEventIn
from app.services.exceptions import ParkingSessionNotFound


async def retrieve_parking_session(
    db: AsyncSession, parking_session_id: int
) -> ParkingSession:
    existing = await db.execute(
        select(ParkingSession)
        .where(ParkingSession.id == parking_session_id)
        .options(selectinload(ParkingSession.payment))
    )
    session = existing.scalar_one_or_none()

    if session is None:
        raise ParkingSessionNotFound()

    return session


async def close_session(
    db: AsyncSession, session: ParkingSession, payload: GateEventIn
) -> None:
    session.exit_time = payload.timestamp
    session.exit_gate_id = payload.gate_id
    session.status = SessionStatus.closed
    session.closed_at = payload.timestamp
    await db.commit()


async def create_session_from_reservation(
    db: AsyncSession, reservation: Reservation, payload: GateEventIn
) -> ParkingSession:
    new_session = ParkingSession(
        parking_lot_id=payload.parking_lot_id,
        reservation_id=reservation.id,
        license_plate=payload.license_plate,
        entry_time=payload.timestamp,
        entry_gate_id=payload.gate_id,
    )
    new_session.payment = Payment(status=PaymentStatus.pending)
    db.add(new_session)
    await db.flush()  # get PK
    await db.commit()
    await db.refresh(new_session)
    return new_session


async def create_session_anonymously(
    db: AsyncSession, payload: GateEventIn
) -> ParkingSession:
    new_session = ParkingSession(
        parking_lot_id=payload.parking_lot_id,
        license_plate=payload.license_plate,
        entry_time=payload.timestamp,
        entry_gate_id=payload.gate_id,
    )
    new_session.payment = Payment(status=PaymentStatus.pending)
    db.add(new_session)
    await db.flush()  # get PK
    await db.commit()
    await db.refresh(new_session)
    return new_session


async def try_get_active_session_by_plate(
    db: AsyncSession, lot_id: int, plate: str
) -> Optional[ParkingSession]:
    q = (
        select(ParkingSession)
        .where(
            ParkingSession.parking_lot_id == lot_id,
            ParkingSession.license_plate == plate,
            ParkingSession.status == SessionStatus.active,
        )
        .options(selectinload(ParkingSession.payment))
    )
    res = await db.execute(q)
    return res.scalar_one_or_none()
