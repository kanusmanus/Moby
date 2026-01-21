from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.parking_lot import ParkingLot
from app.scripts.import_common import ImportContext, load_json, pick, commit_every


def _find_existing_lot(db: Session, name: str, address: str) -> ParkingLot | None:
    return (
        db.query(ParkingLot)
        .filter(ParkingLot.name == name)
        .filter(ParkingLot.address == address)
        .first()
    )


def import_parking_lots(
    db: Session, ctx: ImportContext, filename: str = "parking_lots.json"
) -> None:
    """
    Expected JSON item keys (flexible):
    - id / lot_id
    - name, location, address
    - capacity, reserved
    - tariff, daytariff
    - latitude, longitude
    """
    items = load_json(filename)

    for i, item in enumerate(items, start=1):
        old_id = pick(item, "id", "lot_id", "parking_lot_id", "parkingLotId")

        name = pick(item, "name")
        address = pick(item, "address")
        location = pick(item, "location", default="")
        if not name or not address:
            raise ValueError(f"ParkingLot missing name/address: {item}")

        lot = _find_existing_lot(db, name=name, address=address)
        if not lot:
            lot = ParkingLot(
                name=name,
                location=location,
                address=address,
                capacity=int(pick(item, "capacity", default=0) or 0),
                reserved=int(pick(item, "reserved", default=0) or 0),
                tariff=float(pick(item, "tariff", default=0.0) or 0.0),
                daytariff=float(
                    pick(item, "daytariff", "day_tariff", default=0.0) or 0.0
                ),
                latitude=float(pick(item, "latitude", "lat", default=0.0) or 0.0),
                longitude=float(
                    pick(item, "longitude", "lng", "lon", default=0.0) or 0.0
                ),
            )
            db.add(lot)
            db.flush()

        if old_id is not None:
            ctx.lot_id_map[old_id] = lot.id

        commit_every(db, i, chunk=500)

    db.commit()
