from __future__ import annotations

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.payment import Payment, PaymentStatus
from app.models.parking_session import ParkingSession
from app.scripts.import_common import (
    ImportContext,
    load_json,
    pick,
    parse_dt,
    commit_every,
)


def _parse_status(value) -> PaymentStatus:
    """Parse payment status from legacy data."""
    if value is None:
        return PaymentStatus.pending
    s = str(value).lower().strip()
    if s in ("paid", "completed", "success"):
        return PaymentStatus.paid
    return PaymentStatus.pending


def import_payments(
    db: Session, ctx: ImportContext, filename: str = "payments.json"
) -> None:
    """
    Import payments from legacy JSON.
    
    BELANGRIJK: Het Payment model heeft de volgende velden:
    - id (PK)
    - user_id (FK, nullable)
    - reservation_id (FK, nullable)  
    - session_id (FK, NOT NULL, UNIQUE) <-- VERPLICHT!
    - amount (float, nullable)
    - created_at (datetime)
    - status (enum: pending/paid)
    - completed_at (datetime, nullable)
    
    NIET aanwezig (verwijderd uit oude versie):
    - transaction
    - initiator
    - hash
    - t_data
    
    Expected JSON item keys:
    - id / payment_id
    - user_id (old)
    - reservation_id (old, optional)
    - session_id (old) - VERPLICHT voor koppeling
    - amount
    - status
    - completed_at
    """
    items = load_json(filename)

    for i, item in enumerate(items, start=1):
        old_id = pick(item, "id", "payment_id", "paymentId")
        
        # User mapping (optional)
        old_user_id = pick(item, "user_id", "userId")
        user_id = None
        if old_user_id is not None and old_user_id in ctx.user_id_map:
            user_id = ctx.user_id_map[old_user_id]

        # Reservation mapping (optional)
        old_res_id = pick(item, "reservation_id", "reservationId")
        reservation_id = None
        if old_res_id is not None and old_res_id in ctx.reservation_id_map:
            reservation_id = ctx.reservation_id_map.get(old_res_id)

        # Session mapping - VERPLICHT!
        # Payments moeten gekoppeld zijn aan een session
        old_session_id = pick(item, "session_id", "sessionId", "parking_session_id")
        if old_session_id is None:
            print(f"WARNING: Payment missing session_id, skipping: {item}")
            continue
            
        # Zoek session op basis van oude data (dit moet je aanpassen aan je migratie strategie)
        # Optie 1: Als je een session_id_map hebt
        # session_id = ctx.session_id_map.get(old_session_id)
        
        # Optie 2: Maak een nieuwe session aan of zoek bestaande
        # Voor nu skippen we payments zonder geldige session
        print(f"WARNING: Session mapping not implemented for payment {old_id}")
        continue

        # Check voor duplicaat (op basis van session_id, want die is UNIQUE)
        existing = db.execute(
            select(Payment).where(Payment.session_id == session_id)
        ).scalar_one_or_none()
        
        if existing:
            print(f"Payment for session {session_id} already exists, updating...")
            existing.user_id = user_id
            existing.reservation_id = reservation_id
            existing.amount = float(pick(item, "amount", default=0.0) or 0.0)
            existing.status = _parse_status(pick(item, "status"))
            existing.completed_at = parse_dt(pick(item, "completed_at", "completedAt"))
            
            if old_id is not None:
                ctx.payment_id_map[old_id] = existing.id
        else:
            payment = Payment(
                user_id=user_id,
                reservation_id=reservation_id,
                session_id=session_id,  # VERPLICHT!
                amount=float(pick(item, "amount", default=0.0) or 0.0),
                status=_parse_status(pick(item, "status")),
                completed_at=parse_dt(pick(item, "completed_at", "completedAt")),
            )
            db.add(payment)
            db.flush()

            if old_id is not None:
                ctx.payment_id_map[old_id] = payment.id

        commit_every(db, i, chunk=500)

    db.commit()