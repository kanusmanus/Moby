from httpx import AsyncClient
import pytest

from app.models.parking_lot import ParkingLot
from app.models.user import User
from app.schemas.parking_lot import ParkingLotIn, ParkingLotOut


@pytest.mark.anyio
async def test_get_lot(
    async_client: AsyncClient, lot_in_db: ParkingLot, auth_headers_user: dict[str, str]
):
    resp = await async_client.get(
        f"/parking_lots/{lot_in_db.id}", headers=auth_headers_user
    )

    assert resp.status_code == 200
    data = ParkingLotOut.model_validate(resp.json())
    assert data.id == lot_in_db.id


@pytest.mark.anyio
async def test_create_lot_authorized(
    async_client: AsyncClient, auth_headers_admin: dict[str, str], admin_in_db: User
):
    name = "TestLot"
    payload = ParkingLotIn(
        name=name,
        location="Rotterdam",
        address="Wijnhaven 103",
        capacity=20,
        created_by=admin_in_db.id,
        reserved=0,
        tariff=5.0,
        daytariff=30.0,
        latitude=51.926517,
        longitude=4.462456,
    )
    resp = await async_client.post(
        "/parking_lots",
        json=payload.model_dump(mode="json"),
        headers=auth_headers_admin,
    )

    # Expect 201 (Created)
    assert resp.status_code == 201
    data = ParkingLotOut.model_validate(resp.json())
    assert data.name == name


@pytest.mark.anyio
async def test_create_lot_unauthorized(
    async_client: AsyncClient, auth_headers_user: dict[str, str], user_in_db: User
):
    name = "TestLot"
    payload = ParkingLotIn(
        name=name,
        location="Rotterdam",
        address="Wijnhaven 103",
        capacity=20,
        created_by=user_in_db.id,
        reserved=0,
        tariff=5.0,
        daytariff=30.0,
        latitude=51.926517,
        longitude=4.462456,
    )
    resp = await async_client.post(
        "/parking_lots",
        json=payload.model_dump(mode="json"),
        headers=auth_headers_user,
    )

    # Expect 403 (Forbidden)
    assert resp.status_code == 403


@pytest.mark.anyio
async def test_create_lot_hotel_manager(
    async_client: AsyncClient,
    auth_headers_hotel_manager: dict[str, str],
    hotel_manager_in_db: User,
):
    name = "HotelLot"
    payload = ParkingLotIn(
        name=name,
        location="Rotterdam",
        address="Hotellaan 23",
        capacity=20,
        created_by=hotel_manager_in_db.id,
        reserved=0,
        tariff=5.0,
        daytariff=30.0,
        latitude=51.926517,
        longitude=4.462456,
    )
    resp = await async_client.post(
        "/parking_lots",
        json=payload.model_dump(mode="json"),
        headers=auth_headers_hotel_manager,
    )

    # Expect 201 (Created)
    assert resp.status_code == 201


@pytest.mark.anyio
async def test_update_lot_authorized_admin(
    async_client: AsyncClient, auth_headers_admin: dict[str, str], admin_in_db: User
):
    # Create first
    create_payload = ParkingLotIn(
        name="LotToUpdate",
        location="Rotterdam",
        address="Wijnhaven 103",
        capacity=20,
        created_by=admin_in_db.id,
        reserved=0,
        tariff=5.0,
        daytariff=30.0,
        latitude=51.926517,
        longitude=4.462456,
    )
    resp_create = await async_client.post(
        "/parking_lots",
        json=create_payload.model_dump(mode="json"),
        headers=auth_headers_admin,
    )
    assert resp_create.status_code == 201
    created = ParkingLotOut.model_validate(resp_create.json())

    # Update
    update_payload = ParkingLotIn(
        name="LotUpdated",
        location="Amsterdam",
        address="Damrak 1",
        capacity=50,
        created_by=admin_in_db.id,
        reserved=2,
        tariff=7.5,
        daytariff=45.0,
        latitude=52.373169,
        longitude=4.890660,
    )
    resp_update = await async_client.put(
        f"/parking_lots/{created.id}",
        json=update_payload.model_dump(mode="json"),
        headers=auth_headers_admin,
    )

    assert resp_update.status_code == 200
    updated = ParkingLotOut.model_validate(resp_update.json())
    assert updated.id == created.id
    assert updated.name == "LotUpdated"
    assert updated.location == "Amsterdam"
    assert updated.capacity == 50
    assert updated.tariff == 7.5


@pytest.mark.anyio
async def test_update_lot_authorized_hotel_manager(
    async_client: AsyncClient,
    auth_headers_hotel_manager: dict[str, str],
    hotel_manager_in_db: User,
):
    # Create as hotel_manager (allowed)
    create_payload = ParkingLotIn(
        name="LotToUpdateHM",
        location="Rotterdam",
        address="Wijnhaven 103",
        capacity=10,
        created_by=hotel_manager_in_db.id,
        reserved=0,
        tariff=4.0,
        daytariff=25.0,
        latitude=51.926517,
        longitude=4.462456,
    )
    resp_create = await async_client.post(
        "/parking_lots",
        json=create_payload.model_dump(mode="json"),
        headers=auth_headers_hotel_manager,
    )
    assert resp_create.status_code == 201
    created = ParkingLotOut.model_validate(resp_create.json())

    # Update as hotel_manager (allowed)
    update_payload = ParkingLotIn(
        name="LotUpdatedHM",
        location="Utrecht",
        address="Stationsplein 1",
        capacity=12,
        created_by=hotel_manager_in_db.id,
        reserved=1,
        tariff=4.5,
        daytariff=28.0,
        latitude=52.089444,
        longitude=5.110278,
    )
    resp_update = await async_client.put(
        f"/parking_lots/{created.id}",
        json=update_payload.model_dump(mode="json"),
        headers=auth_headers_hotel_manager,
    )
    assert resp_update.status_code == 200
    updated = ParkingLotOut.model_validate(resp_update.json())
    assert updated.name == "LotUpdatedHM"
    assert updated.location == "Utrecht"


@pytest.mark.anyio
async def test_update_lot_unauthorized_user(
    async_client: AsyncClient,
    auth_headers_admin: dict[str, str],
    auth_headers_user: dict[str, str],
    admin_in_db: User,
):
    # Create as admin
    create_payload = ParkingLotIn(
        name="LotToUpdateForbidden",
        location="Rotterdam",
        address="Wijnhaven 103",
        capacity=20,
        created_by=admin_in_db.id,
        reserved=0,
        tariff=5.0,
        daytariff=30.0,
        latitude=51.926517,
        longitude=4.462456,
    )
    resp_create = await async_client.post(
        "/parking_lots",
        json=create_payload.model_dump(mode="json"),
        headers=auth_headers_admin,
    )
    assert resp_create.status_code == 201
    created = ParkingLotOut.model_validate(resp_create.json())

    # Update as regular user (forbidden)
    update_payload = ParkingLotIn(
        name="ShouldNotUpdate",
        location="Rotterdam",
        address="Wijnhaven 103",
        capacity=99,
        created_by=admin_in_db.id,
        reserved=0,
        tariff=99.0,
        daytariff=999.0,
        latitude=51.9,
        longitude=4.4,
    )
    resp_update = await async_client.put(
        f"/parking_lots/{created.id}",
        json=update_payload.model_dump(mode="json"),
        headers=auth_headers_user,
    )
    assert resp_update.status_code == 403


@pytest.mark.anyio
async def test_update_lot_not_found(
    async_client: AsyncClient, auth_headers_admin: dict[str, str], admin_in_db: User
):
    update_payload = ParkingLotIn(
        name="DoesNotExist",
        location="Rotterdam",
        address="Wijnhaven 103",
        capacity=20,
        created_by=admin_in_db.id,
        reserved=0,
        tariff=5.0,
        daytariff=30.0,
        latitude=51.926517,
        longitude=4.462456,
    )

    resp_update = await async_client.put(
        "/parking_lots/999999",
        json=update_payload.model_dump(mode="json"),
        headers=auth_headers_admin,
    )
    assert resp_update.status_code == 404


@pytest.mark.anyio
async def test_delete_lot_authorized_admin(
    async_client: AsyncClient, auth_headers_admin: dict[str, str], admin_in_db: User
):
    # Create
    create_payload = ParkingLotIn(
        name="LotToDelete",
        location="Rotterdam",
        address="Wijnhaven 103",
        capacity=20,
        created_by=admin_in_db.id,
        reserved=0,
        tariff=5.0,
        daytariff=30.0,
        latitude=51.926517,
        longitude=4.462456,
    )
    resp_create = await async_client.post(
        "/parking_lots",
        json=create_payload.model_dump(mode="json"),
        headers=auth_headers_admin,
    )
    assert resp_create.status_code == 201
    created = ParkingLotOut.model_validate(resp_create.json())

    # Delete
    resp_delete = await async_client.delete(
        f"/parking_lots/{created.id}",
        headers=auth_headers_admin,
    )
    assert resp_delete.status_code == 204

    # (Optional) verify it's gone: update should 404
    update_payload = ParkingLotIn(
        name="Whatever",
        location="Rotterdam",
        address="Wijnhaven 103",
        capacity=1,
        created_by=admin_in_db.id,
        reserved=0,
        tariff=1.0,
        daytariff=1.0,
        latitude=51.9,
        longitude=4.4,
    )
    resp_update = await async_client.put(
        f"/parking_lots/{created.id}",
        json=update_payload.model_dump(mode="json"),
        headers=auth_headers_admin,
    )
    assert resp_update.status_code == 404


@pytest.mark.anyio
async def test_delete_lot_authorized_hotel_manager(
    async_client: AsyncClient,
    auth_headers_hotel_manager: dict[str, str],
    hotel_manager_in_db: User,
):
    # Create
    create_payload = ParkingLotIn(
        name="LotToDeleteHM",
        location="Rotterdam",
        address="Wijnhaven 103",
        capacity=15,
        created_by=hotel_manager_in_db.id,
        reserved=0,
        tariff=5.0,
        daytariff=30.0,
        latitude=51.926517,
        longitude=4.462456,
    )
    resp_create = await async_client.post(
        "/parking_lots",
        json=create_payload.model_dump(mode="json"),
        headers=auth_headers_hotel_manager,
    )
    assert resp_create.status_code == 201
    created = ParkingLotOut.model_validate(resp_create.json())

    # Delete
    resp_delete = await async_client.delete(
        f"/parking_lots/{created.id}",
        headers=auth_headers_hotel_manager,
    )
    assert resp_delete.status_code == 204


@pytest.mark.anyio
async def test_delete_lot_unauthorized_user(
    async_client: AsyncClient,
    auth_headers_admin: dict[str, str],
    auth_headers_user: dict[str, str],
    admin_in_db: User,
):
    # Create as admin
    create_payload = ParkingLotIn(
        name="LotToDeleteForbidden",
        location="Rotterdam",
        address="Wijnhaven 103",
        capacity=20,
        created_by=admin_in_db.id,
        reserved=0,
        tariff=5.0,
        daytariff=30.0,
        latitude=51.926517,
        longitude=4.462456,
    )
    resp_create = await async_client.post(
        "/parking_lots",
        json=create_payload.model_dump(mode="json"),
        headers=auth_headers_admin,
    )
    assert resp_create.status_code == 201
    created = ParkingLotOut.model_validate(resp_create.json())

    # Delete as regular user (forbidden)
    resp_delete = await async_client.delete(
        f"/parking_lots/{created.id}",
        headers=auth_headers_user,
    )
    assert resp_delete.status_code == 403


@pytest.mark.anyio
async def test_delete_lot_not_found(
    async_client: AsyncClient,
    auth_headers_admin: dict[str, str],
):
    resp_delete = await async_client.delete(
        "/parking_lots/999999",
        headers=auth_headers_admin,
    )
    assert resp_delete.status_code == 404
