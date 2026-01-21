from __future__ import annotations

from app.db.session import SessionLocal
from app.scripts.import_common import ImportContext

from app.scripts.import_users import import_users
from app.scripts.import_parking_lots import import_parking_lots
from app.scripts.import_vehicles import import_vehicles
from app.scripts.import_reservations import import_reservations
from app.scripts.import_payments import import_payments


def main() -> None:
    ctx = ImportContext.empty()
    db = SessionLocal()
    try:
        # Order matters because of foreign keys
        import_users(db, ctx, "users.json")
        import_parking_lots(db, ctx, "parking_lots.json")
        import_vehicles(db, ctx, "vehicles.json")
        import_reservations(db, ctx, "reservations.json")
        import_payments(db, ctx, "payments.json")

        print("Import complete")
        print(
            f"Users={len(ctx.user_id_map)} "
            f"Lots={len(ctx.lot_id_map)} "
            f"Vehicles={len(ctx.vehicle_id_map)} "
            f"Reservations={len(ctx.reservation_id_map)} "
            f"Payments={len(ctx.payment_id_map)}"
        )
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
