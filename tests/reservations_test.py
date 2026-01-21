from datetime import datetime, timedelta
from httpx import AsyncClient
import pytest

from app.models.parking_lot import ParkingLot
from app.models.vehicle import Vehicle
from app.schemas.reservations import ReservationIn


@pytest.mark.anyio
async def test_create_reservation(
    async_client: AsyncClient,
    lot_in_db: ParkingLot,
    vehicle_in_db: Vehicle,
    auth_headers_user: dict[str, str],
):
    payload = ReservationIn(
        planned_start=datetime.now(),
        planned_end=datetime.now() + timedelta(hours=1),
        parking_lot_id=lot_in_db.id,
        vehicle_id=vehicle_in_db.id,
        license_plate=vehicle_in_db.license_plate,
    )

    resp = await async_client.post(
        "/reservations",
        json=payload.model_dump(mode="json"),
        headers=auth_headers_user,
    )

    # Expect 201 (Created) as no overlap should be happening
    assert resp.status_code == 201


@pytest.mark.anyio
async def test_create_reservation_overlap(
    async_client: AsyncClient,
    lot_in_db: ParkingLot,
    vehicle_in_db: Vehicle,
    auth_headers_user: dict[str, str],
):
    payload = ReservationIn(
        planned_start=datetime.now(),
        planned_end=datetime.now() + timedelta(hours=1),
        parking_lot_id=lot_in_db.id,
        vehicle_id=vehicle_in_db.id,
        license_plate=vehicle_in_db.license_plate,
    )
    # Create reservations up to capacity (5)
    for i in range(lot_in_db.capacity):
        resp = await async_client.post(
            "/reservations",
            json=payload.model_dump(mode="json"),
            headers=auth_headers_user,
        )
        # Expect 201 (Created)
        assert resp.status_code == 201, f"Reservation {i + 1} failed"

    resp_overflow = await async_client.post(
        "/reservations",
        json=payload.model_dump(mode="json"),
        headers=auth_headers_user,
    )
    # Expect 409 (Conflict) because of overlapping times
    assert resp_overflow.status_code == 409


@pytest.mark.anyio
async def test_create_reservation_unauthorized(
    async_client: AsyncClient,
):
    payload = ReservationIn(
        planned_start=datetime.now(),
        planned_end=datetime.now() + timedelta(hours=1),
        parking_lot_id=-1,
        vehicle_id=-1,
        license_plate="fake_plate",
    )
    resp = await async_client.post(
        "/reservations",
        json=payload.model_dump(mode="json"),
    )
    # Expect 401 (Unauthorized)
    assert resp.status_code == 401
