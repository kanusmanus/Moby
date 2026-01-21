from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.vehicle import Vehicle
from app.scripts.import_common import ImportContext, load_json, pick, commit_every


def import_vehicles(
    db: Session, ctx: ImportContext, filename: str = "vehicles.json"
) -> None:
    """
    Expected JSON item keys (flexible):
    - id / vehicle_id
    - user_id (old) OR user_email (optional)
    - license_plate
    - make, model, color, year
    """
    items = load_json(filename)

    for i, item in enumerate(items, start=1):
        old_id = pick(item, "id", "vehicle_id", "vehicleId")
        license_plate = pick(item, "license_plate", "licensePlate", "plate")
        if not license_plate:
            raise ValueError(f"Vehicle missing license_plate: {item}")

        # Resolve user_id from old mapping
        old_user_id = pick(item, "user_id", "userId", "owner_id")
        if old_user_id is None or old_user_id not in ctx.user_id_map:
            raise ValueError(
                f"Vehicle user_id not mapped yet. Import users first. item={item}"
            )
        user_id = ctx.user_id_map[old_user_id]

        vehicle = (
            db.query(Vehicle).filter(Vehicle.license_plate == license_plate).first()
        )
        if not vehicle:
            vehicle = Vehicle(
                user_id=user_id,
                license_plate=license_plate,
                make=pick(item, "make", default=""),
                model=pick(item, "model", default=""),
                color=pick(item, "color", default=""),
                year=int(pick(item, "year", default=0) or 0),
            )
            db.add(vehicle)
            db.flush()
        else:
            # keep ownership consistent if old data says different
            vehicle.user_id = user_id

        if old_id is not None:
            ctx.vehicle_id_map[old_id] = vehicle.id

        commit_every(db, i, chunk=500)

    db.commit()
