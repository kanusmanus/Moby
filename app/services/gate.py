from sqlalchemy.ext.asyncio import AsyncSession
from app.models.gate import Gate
from app.models.parking_session import ParkingSession
from app.models.payment import PaymentStatus
from app.models.reservation import Reservation
from app.schemas.gate import (
    GateDecision,
    GateDirection,
    GateEventIn,
    GateEventOut,
    GateIn,
)

from app.services.parking_sessions import (
    close_session,
    create_session_anonymously,
    create_session_from_reservation,
    try_get_active_session_by_plate,
)
from app.services.reservations import try_get_valid_reservation_by_plate

from datetime import datetime


async def handle_gate_event(db: AsyncSession, payload: GateEventIn):
    # Check if reservation exists with license plate
    valid_reservation = await try_get_valid_reservation_by_plate(
        db, payload.parking_lot_id, payload.license_plate, datetime.now()
    )

    # Check if session exists with license plate
    active_session = await try_get_active_session_by_plate(
        db, payload.parking_lot_id, payload.license_plate
    )

    if payload.direction == GateDirection.entry:
        return await handle_gate_entry(db, payload, valid_reservation, active_session)

    if payload.direction == GateDirection.exit:
        return await handle_gate_exit(db, payload, active_session)

    return GateEventOut(
        gate_id=payload.gate_id, decision=GateDecision.deny, reason="invalid_direction"
    )


async def handle_gate_entry(
    db: AsyncSession,
    payload: GateEventIn,
    valid_reservation: Reservation | None,
    active_session: ParkingSession | None,
):
    # If there's already an active session, this is a duplicate entry hit
    if active_session is not None:
        return GateEventOut(
            gate_id=payload.gate_id,
            decision=GateDecision.deny,
            reason="session_already_active",
            session_id=active_session.id,
        )

    # If a valid reservation exists, start a session linked to it
    if valid_reservation:
        new_session = await create_session_from_reservation(
            db, valid_reservation, payload
        )
        return GateEventOut(
            gate_id=payload.gate_id,
            decision=GateDecision.open,
            reason="reservation_valid",
            session_id=new_session.id,
            reservation_id=valid_reservation.id,
        )

    # No reservation -> treat as anonymous drive-up
    session = await create_session_anonymously(db, payload)
    return GateEventOut(
        gate_id=payload.gate_id,
        decision=GateDecision.open,
        reason="anonymous_driveup_started",
        session_id=session.id,
    )


async def handle_gate_exit(
    db: AsyncSession, payload: GateEventIn, active_session: ParkingSession | None
):
    # To exit you must have an active session
    # But we don't want to trap people
    if not active_session:
        print("No active session found")
        return GateEventOut(
            gate_id=payload.gate_id,
            decision=GateDecision.open,
            reason="no_active_session",
        )

    print("Active session found")
    # Check if session is actually paid
    if active_session.payment.status != PaymentStatus.paid:
        return GateEventOut(
            gate_id=payload.gate_id,
            decision=GateDecision.deny,
            reason="session_not_paid",
        )

    await close_session(db, active_session, payload)
    return GateEventOut(
        gate_id=payload.gate_id,
        decision=GateDecision.open,
        reason="session_closed",
        session_id=active_session.id,
    )


async def create_gate(db: AsyncSession, payload: GateIn) -> Gate:
    new_gate = Gate(parking_lot_id=payload.parking_lot_id)
    db.add(new_gate)
    await db.flush()  # get PK
    await db.commit()
    await db.refresh(new_gate)
    return new_gate
