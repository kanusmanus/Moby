from httpx import AsyncClient
import pytest

from app.models.vehicle import Vehicle
from app.schemas.vehicle import VehicleIn, VehicleOut


@pytest.mark.anyio
async def test_create_vehicle(
    async_client: AsyncClient,
    auth_headers_user: dict[str, str],
):
    """Test creating a vehicle."""
    payload = VehicleIn(
        license_plate="AB-123-CD",
        make="Toyota",
        model="Corolla",
        color="Blue",
        year=2020,
    )

    resp = await async_client.post(
        "/vehicles",
        json=payload.model_dump(mode="json"),
        headers=auth_headers_user,
    )

    assert resp.status_code == 201
    data = VehicleOut.model_validate(resp.json())
    assert data.license_plate == "AB-123-CD"
    assert data.make == "Toyota"


@pytest.mark.anyio
async def test_create_vehicle_duplicate_plate(
    async_client: AsyncClient,
    auth_headers_user: dict[str, str],
):
    """Test creating a vehicle with duplicate license plate."""
    payload = VehicleIn(
        license_plate="DUPLICATE",
        make="Toyota",
        model="Corolla",
        color="Blue",
        year=2020,
    )

    # Create first vehicle
    resp1 = await async_client.post(
        "/vehicles",
        json=payload.model_dump(mode="json"),
        headers=auth_headers_user,
    )
    assert resp1.status_code == 201

    # Try to create duplicate
    resp2 = await async_client.post(
        "/vehicles",
        json=payload.model_dump(mode="json"),
        headers=auth_headers_user,
    )
    assert resp2.status_code == 409


@pytest.mark.anyio
async def test_list_user_vehicles(
    async_client: AsyncClient,
    vehicle_in_db: Vehicle,
    auth_headers_user: dict[str, str],
):
    """Test listing user's vehicles."""
    resp = await async_client.get(
        "/vehicles",
        headers=auth_headers_user,
    )

    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(v["id"] == vehicle_in_db.id for v in data)


@pytest.mark.anyio
async def test_get_vehicle(
    async_client: AsyncClient,
    vehicle_in_db: Vehicle,
    auth_headers_user: dict[str, str],
):
    """Test getting a specific vehicle."""
    resp = await async_client.get(
        f"/vehicles/{vehicle_in_db.id}",
        headers=auth_headers_user,
    )

    assert resp.status_code == 200
    data = VehicleOut.model_validate(resp.json())
    assert data.id == vehicle_in_db.id


@pytest.mark.anyio
async def test_update_vehicle(
    async_client: AsyncClient,
    vehicle_in_db: Vehicle,
    auth_headers_user: dict[str, str],
):
    """Test updating a vehicle."""
    payload = VehicleIn(
        license_plate=vehicle_in_db.license_plate,
        make="Honda",  # Changed
        model="Civic",  # Changed
        color="Red",  # Changed
        year=2021,  # Changed
    )

    resp = await async_client.put(
        f"/vehicles/{vehicle_in_db.id}",
        json=payload.model_dump(mode="json"),
        headers=auth_headers_user,
    )

    assert resp.status_code == 200
    data = VehicleOut.model_validate(resp.json())
    assert data.make == "Honda"
    assert data.model == "Civic"


@pytest.mark.anyio
async def test_delete_vehicle(
    async_client: AsyncClient,
    vehicle_in_db: Vehicle,
    auth_headers_user: dict[str, str],
):
    """Test deleting a vehicle."""
    resp = await async_client.delete(
        f"/vehicles/{vehicle_in_db.id}",
        headers=auth_headers_user,
    )

    assert resp.status_code == 204

    # Verify it's deleted
    resp_get = await async_client.get(
        f"/vehicles/{vehicle_in_db.id}",
        headers=auth_headers_user,
    )
    assert resp_get.status_code == 404


@pytest.mark.anyio
async def test_create_vehicle_unauthorized(async_client: AsyncClient):
    """Test creating a vehicle without auth."""
    payload = VehicleIn(
        license_plate="NOAUTH",
        make="Toyota",
        model="Corolla",
        color="Blue",
        year=2020,
    )

    resp = await async_client.post(
        "/vehicles",
        json=payload.model_dump(mode="json"),
    )

    assert resp.status_code == 401
