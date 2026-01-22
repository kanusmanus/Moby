from datetime import datetime, timedelta
from httpx import AsyncClient
import pytest

from app.models.parking_lot import ParkingLot
from app.models.reservation import Reservation
from app.models.user import User
from app.models.vehicle import Vehicle
from app.schemas.reservations import ReservationIn, ReservationOut


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


@pytest.mark.anyio
async def test_get_reservation_owner(
    async_client: AsyncClient,
    reservation_in_db: Reservation,
    auth_headers_user: dict[str, str],
):
    """Test that owner can get their own reservation."""
    resp = await async_client.get(
        f"/reservations/{reservation_in_db.id}",
        headers=auth_headers_user,
    )
    assert resp.status_code == 200
    data = ReservationOut.model_validate(resp.json())
    assert data.id == reservation_in_db.id


@pytest.mark.anyio
async def test_get_reservation_admin(
    async_client: AsyncClient,
    reservation_in_db: Reservation,
    auth_headers_admin: dict[str, str],
):
    """Test that admin can get any reservation."""
    resp = await async_client.get(
        f"/reservations/{reservation_in_db.id}",
        headers=auth_headers_admin,
    )
    assert resp.status_code == 200
    data = ReservationOut.model_validate(resp.json())
    assert data.id == reservation_in_db.id


@pytest.mark.anyio
async def test_get_reservation_not_found(
    async_client: AsyncClient,
    auth_headers_user: dict[str, str],
):
    """Test getting a non-existent reservation."""
    resp = await async_client.get(
        "/reservations/999999",
        headers=auth_headers_user,
    )
    assert resp.status_code == 404


@pytest.mark.anyio
async def test_delete_reservation_owner(
    async_client: AsyncClient,
    reservation_in_db: Reservation,
    auth_headers_user: dict[str, str],
):
    """Test that owner can delete their own reservation."""
    resp = await async_client.delete(
        f"/reservations/{reservation_in_db.id}",
        headers=auth_headers_user,
    )
    assert resp.status_code == 204

    # Verify it's deleted
    resp_get = await async_client.get(
        f"/reservations/{reservation_in_db.id}",
        headers=auth_headers_user,
    )
    assert resp_get.status_code == 404


@pytest.mark.anyio
async def test_delete_reservation_admin(
    async_client: AsyncClient,
    reservation_in_db: Reservation,
    auth_headers_admin: dict[str, str],
):
    """Test that admin can delete any reservation."""
    resp = await async_client.delete(
        f"/reservations/{reservation_in_db.id}",
        headers=auth_headers_admin,
    )
    assert resp.status_code == 204

    # Verify it's deleted
    resp_get = await async_client.get(
        f"/reservations/{reservation_in_db.id}",
        headers=auth_headers_admin,
    )
    assert resp_get.status_code == 404


@pytest.mark.anyio
async def test_delete_reservation_not_owner(
    async_client: AsyncClient,
    reservation_in_db: Reservation,
    auth_headers_hotel_manager: dict[str, str],
):
    """Test that non-owner/non-admin cannot delete someone else's reservation."""
    resp = await async_client.delete(
        f"/reservations/{reservation_in_db.id}",
        headers=auth_headers_hotel_manager,
    )
    assert resp.status_code == 403


@pytest.mark.anyio
async def test_delete_reservation_not_found(
    async_client: AsyncClient,
    auth_headers_user: dict[str, str],
):
    """Test deleting a non-existent reservation."""
    resp = await async_client.delete(
        "/reservations/999999",
        headers=auth_headers_user,
    )
    assert resp.status_code == 404


@pytest.mark.anyio
async def test_delete_reservation_unauthorized(
    async_client: AsyncClient,
    reservation_in_db: Reservation,
):
    """Test deleting without auth."""
    resp = await async_client.delete(
        f"/reservations/{reservation_in_db.id}",
    )
    assert resp.status_code == 401