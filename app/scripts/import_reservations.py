from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.reservation import Reservation, ReservationStatus, ReservationChannel
from app.scripts.import_common import (
    ImportContext,
    load_json,
    pick,
    parse_dt,
    commit_every,
)


def _parse_status(value) -> ReservationStatus:
    if value is None:
        return ReservationStatus.confirmed
    s = str(value).lower().strip()
    if s in ("pending",):
        return ReservationStatus.pending
    if s in ("confirmed", "confirm", "active"):
        return ReservationStatus.confirmed
    if s in ("cancelled", "canceled", "cancel"):
        return ReservationStatus.cancelled
    if s in ("expired",):
        return ReservationStatus.expired
    if s in ("completed",):
        return ReservationStatus.completed
    return ReservationStatus.confirmed


def import_reservations(
    db: Session, ctx: ImportContext, filename: str = "reservations.json"
) -> None:
    """
    Expected JSON item keys (flexible):
    - id / reservation_id
    - user_id (old), vehicle_id (old), parking_lot_id (old)
    - start_time / planned_start, end_time / planned_end (iso string or timestamp)
    - status
    - cost / quoted_cost / original_cost
    - license_plate
    """
    items = load_json(filename)

    for i, item in enumerate(items, start=1):
        old_id = pick(item, "id", "reservation_id", "reservationId")

        old_user_id = pick(item, "user_id", "userId")
        old_vehicle_id = pick(item, "vehicle_id", "vehicleId")
        old_lot_id = pick(item, "parking_lot_id", "parkingLotId", "lot_id")

        if old_user_id not in ctx.user_id_map:
            raise ValueError(f"Reservation user_id not mapped. item={item}")
        if old_vehicle_id not in ctx.vehicle_id_map:
            raise ValueError(f"Reservation vehicle_id not mapped. item={item}")
        if old_lot_id not in ctx.lot_id_map:
            raise ValueError(f"Reservation parking_lot_id not mapped. item={item}")

        planned_start = parse_dt(pick(item, "planned_start", "start_time", "startTime", "start"))
        planned_end = parse_dt(pick(item, "planned_end", "end_time", "endTime", "end"))
        
        if not planned_start or not planned_end:
            raise ValueError(f"Reservation missing start/end time: {item}")

        license_plate = pick(item, "license_plate", "licensePlate", "plate", default="UNKNOWN")
        original_cost = float(pick(item, "original_cost", "cost", "price", default=0.0) or 0.0)
        quoted_cost = float(pick(item, "quoted_cost", "cost", "price", default=0.0) or 0.0)
        discount_amount = float(pick(item, "discount_amount", default=0.0) or 0.0)

        reservation = Reservation(
            user_id=ctx.user_id_map[old_user_id],
            vehicle_id=ctx.vehicle_id_map[old_vehicle_id],
            parking_lot_id=ctx.lot_id_map[old_lot_id],
            license_plate=license_plate,
            planned_start=planned_start,
            planned_end=planned_end,
            status=_parse_status(pick(item, "status")),
            channel=ReservationChannel.registered,
            quoted_cost=quoted_cost,
            original_cost=original_cost,
            discount_amount=discount_amount,
        )
        db.add(reservation)
        db.flush()

        if old_id is not None:
            ctx.reservation_id_map[old_id] = reservation.id

        commit_every(db, i, chunk=500)

    db.commit()