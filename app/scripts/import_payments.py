from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.payment import Payment
from app.scripts.import_common import (
    ImportContext,
    load_json,
    pick,
    parse_dt,
    commit_every,
)


def import_payments(
    db: Session, ctx: ImportContext, filename: str = "payments.json"
) -> None:
    """
    Expected JSON item keys (flexible):
    - id / payment_id
    - user_id (old)
    - reservation_id (old, optional)
    - transaction (unique)
    - amount
    - initiator
    - completed_at
    - hash
    - t_data (dict)
    """
    items = load_json(filename)

    for i, item in enumerate(items, start=1):
        old_id = pick(item, "id", "payment_id", "paymentId")
        transaction = pick(item, "transaction", "transaction_id", "transactionId")
        if not transaction:
            raise ValueError(f"Payment missing transaction: {item}")

        old_user_id = pick(item, "user_id", "userId")
        if old_user_id not in ctx.user_id_map:
            raise ValueError(f"Payment user_id not mapped. item={item}")
        user_id = ctx.user_id_map[old_user_id]

        old_res_id = pick(item, "reservation_id", "reservationId")
        reservation_id = None
        if old_res_id is not None:
            reservation_id = ctx.reservation_id_map.get(old_res_id)

        existing = db.query(Payment).filter(Payment.transaction == transaction).first()
        if not existing:
            payment = Payment(
                user_id=user_id,
                reservation_id=reservation_id,
                transaction=transaction,
                amount=float(pick(item, "amount", default=0.0) or 0.0),
                initiator=pick(item, "initiator"),
                completed_at=parse_dt(pick(item, "completed_at", "completedAt")),
                hash=pick(item, "hash"),
                t_data=pick(item, "t_data", "tData"),
            )
            db.add(payment)
            db.flush()
        else:
            # keep links consistent
            existing.user_id = user_id
            existing.reservation_id = reservation_id

        # map old -> new (for completeness)
        if old_id is not None:
            ctx.payment_id_map[old_id] = existing.id if existing else payment.id

        commit_every(db, i, chunk=500)

    db.commit()
