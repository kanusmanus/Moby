from datetime import datetime, timedelta, timezone
from typing import AsyncGenerator
import asyncio
import jwt
import pytest
import httpx
import os
import string
import random
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.main import app
from app.db.base import Base
from app.db import session as db_session
from app.models.gate import Gate
from app.models.parking_lot import ParkingLot
from app.models.reservation import Reservation
from app.models.user import User, UserRole
from app.models.vehicle import Vehicle
from app.services.auth import JWT_ALG, JWT_SECRET


TEST_DB_URL = os.getenv(
    "DATABASE_URL_TEST",
    "postgresql+asyncpg://app:IboIsIbrahim@localhost:5432/app_test_db",
)
engine = create_async_engine(TEST_DB_URL, future=True)
TestingSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


@pytest.fixture
def anyio_backend():
    # this tells pytest-anyio: run tests only with asyncio, not trio
    return "asyncio"


@pytest.fixture
async def async_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    # 1. create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 2. override dependency, capturing THIS sessionmaker
    async def override_get_db():
        async with TestingSessionLocal() as s:
            yield s

    app.dependency_overrides[db_session.get_session] = override_get_db

    # 3. create client with ASGI transport
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    # 4. cleanup
    app.dependency_overrides.clear()
    await engine.dispose()


@pytest.fixture
async def async_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocal() as session:
        yield session


@pytest.fixture(scope="session", autouse=True)
def reset_test_database_once():
    """
    Drop + recreate all tables in the TEST database once
    before the test session starts (both locally and in CI).
    Synchronous wrapper so it doesn't depend on anyio_backend.
    """

    async def _reset():
        engine = create_async_engine(TEST_DB_URL, future=True)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        await engine.dispose()

    asyncio.run(_reset())
    yield


async def create_user(async_session: AsyncSession, email: str, role: UserRole):
    result = await async_session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if user:
        return user

    user = User(
        username=email,
        password_hash="test",
        name=email,
        email=email,
        phone="683713498",
        role=role,
        active=True,
        birth_year=2001,
    )
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)
    return user


@pytest.fixture
async def user_in_db(async_session: AsyncSession) -> User:
    return await create_user(async_session, "user@test.com", UserRole.user)


@pytest.fixture
async def admin_in_db(async_session: AsyncSession) -> User:
    return await create_user(async_session, "admin@test.com", UserRole.admin)


@pytest.fixture
async def parking_meter_in_db(async_session: AsyncSession) -> User:
    return await create_user(async_session, "parking@meter.com", UserRole.parking_meter)


@pytest.fixture
async def hotel_manager_in_db(async_session: AsyncSession) -> User:
    return await create_user(async_session, "hotel@manager.com", UserRole.hotel_manager)


def create_token(user: User) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user.id),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=30)).timestamp()),
    }

    return jwt.encode(
        payload,
        JWT_SECRET,
        algorithm=JWT_ALG,
    )


@pytest.fixture
def token_for_user(user_in_db: User) -> str:
    return create_token(user_in_db)


@pytest.fixture
def token_for_admin(admin_in_db: User) -> str:
    return create_token(admin_in_db)


@pytest.fixture
def token_for_parking_meter(parking_meter_in_db: User) -> str:
    return create_token(parking_meter_in_db)


@pytest.fixture
def token_for_hotel_manager(hotel_manager_in_db: User) -> str:
    return create_token(hotel_manager_in_db)


@pytest.fixture
def auth_headers_user(token_for_user: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token_for_user}"}


@pytest.fixture
def auth_headers_admin(token_for_admin: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token_for_admin}"}


@pytest.fixture
def auth_headers_parking_meter(token_for_parking_meter: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token_for_parking_meter}"}


@pytest.fixture
def auth_headers_hotel_manager(token_for_hotel_manager: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token_for_hotel_manager}"}


@pytest.fixture
async def lot_in_db(async_session: AsyncSession, admin_in_db: User):
    lot = ParkingLot(
        name="TestLot",
        location="Rotterdam",
        address="Wijnhaven 107",
        capacity=5,
        created_by=admin_in_db.id,
        reserved=0,
        tariff=5.0,
        daytariff=30.0,
        latitude=51.926517,
        longitude=4.462456,
    )
    async_session.add(lot)
    await async_session.flush()
    await async_session.commit()
    return lot


@pytest.fixture
async def vehicle_in_db(async_session: AsyncSession, user_in_db: User):
    vehicle = Vehicle(
        user_id=user_in_db.id,
        license_plate="".join(
            random.choices(string.ascii_uppercase + string.digits, k=6)
        ),
        make="BMW",
        model="M5",
        color="Black",
        year=2020,
    )
    async_session.add(vehicle)
    await async_session.flush()
    await async_session.commit()
    return vehicle


@pytest.fixture
async def gate_in_db(async_session: AsyncSession, lot_in_db: ParkingLot):
    gate = Gate(parking_lot_id=lot_in_db.id)
    async_session.add(gate)
    await async_session.flush()
    await async_session.commit()
    return gate


@pytest.fixture
async def reservation_in_db(
    async_session: AsyncSession,
    user_in_db: User,
    lot_in_db: ParkingLot,
    vehicle_in_db: Vehicle,
):
    reservation = Reservation(
        planned_start=datetime.now(),
        planned_end=datetime.now() + timedelta(hours=2),
        user_id=user_in_db.id,
        parking_lot_id=lot_in_db.id,
        vehicle_id=vehicle_in_db.id,
        license_plate=vehicle_in_db.license_plate,
    )
    async_session.add(reservation)
    await async_session.flush()
    await async_session.commit()
    return reservation
