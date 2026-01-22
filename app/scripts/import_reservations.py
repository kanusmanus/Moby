from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.reservation import Reservation, ReservationStatus
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
    return ReservationStatus.confirmed


def import_reservations(
    db: Session, ctx: ImportContext, filename: str = "reservations.json"
) -> None:
    """
    Expected JSON item keys (flexible):
    - id / reservation_id
    - user_id (old), vehicle_id (old), parking_lot_id (old)
    - start_time, end_time (iso string or timestamp)
    - status
    - cost
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

        start_time = parse_dt(pick(item, "start_time", "startTime", "start"))
        end_time = parse_dt(pick(item, "end_time", "endTime", "end"))
        if not start_time or not end_time:
            raise ValueError(f"Reservation missing start/end time: {item}")

        reservation = Reservation(
            user_id=ctx.user_id_map[old_user_id],
            vehicle_id=ctx.vehicle_id_map[old_vehicle_id],
            parking_lot_id=ctx.lot_id_map[old_lot_id],
            start_time=start_time,
            end_time=end_time,
            status=_parse_status(pick(item, "status")),
            cost=float(pick(item, "cost", "price", default=0.0) or 0.0),
        )
        db.add(reservation)
        db.flush()

        if old_id is not None:
            ctx.reservation_id_map[old_id] = reservation.id

        commit_every(db, i, chunk=500)

    db.commit()
