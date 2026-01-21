from httpx import AsyncClient
import pytest

from app.models.user import User
from app.schemas.auth import LoginOut, RegisterIn, RegisterOut, UserOut, UserUpdateIn

EMAIL = "test@test.com"
USERNAME = "test"
NAME = "test"
PASSWORD = "password"
TOKEN_TYPE = "bearer"


@pytest.mark.anyio
async def test_register_valid(async_client: AsyncClient):
    payload = RegisterIn(
        email=EMAIL,
        password=PASSWORD,
        name=NAME,
        username=NAME,
        phone="0612345678",
        active=True,
        birth_year=1990,
    )
    resp = await async_client.post(
        "/auth/register",
        json=payload.model_dump(mode="json"),
    )
    assert resp.status_code == 201
    data = RegisterOut.model_validate(resp.json())
    assert data.email == EMAIL
    assert data.name == NAME
    assert data.id is not None


@pytest.mark.anyio
async def test_register_existing(async_client: AsyncClient):
    payload = RegisterIn(
        email=EMAIL,
        password=PASSWORD,
        name=NAME,
        username=NAME,
        phone="0612345678",
        active=True,
        birth_year=1990,
    )
    resp = await async_client.post(
        "/auth/register", json=payload.model_dump(mode="json")
    )
    # Expect 409 (conflict) because user already exists
    assert resp.status_code == 409


@pytest.mark.anyio
async def test_register_bad_email(async_client: AsyncClient):
    resp = await async_client.post(
        "/auth/register",
        json={
            "email": "hi",
            "password": PASSWORD,
            "name": NAME,
            "username": NAME,
            "phone": "0612345678",
            "active": True,
            "birth_year": 1990,
        },
    )
    # Expect 422 (Unprocessable Entry) because email is invalid
    assert resp.status_code == 422


@pytest.mark.anyio
async def test_login_valid(async_client: AsyncClient):
    resp = await async_client.post(
        "/auth/login",
        json={"email": EMAIL, "password": PASSWORD},
    )
    assert resp.status_code == 200
    data = LoginOut.model_validate(resp.json())
    assert data.token_type == TOKEN_TYPE
    assert data.access_token is not None


@pytest.mark.anyio
async def test_login_invalid(async_client: AsyncClient):
    resp = await async_client.post(
        "/auth/login",
        json={"email": "invalid@gmail.com", "password": "invalid"},
    )
    # Expect 401 (Unauthorized) because user doesn't exist
    assert resp.status_code == 401


@pytest.mark.anyio
async def test_get_user_authorized(
    async_client: AsyncClient, user_in_db: User, auth_headers_admin: dict[str, str]
):
    resp = await async_client.get(
        f"/auth/users/{user_in_db.id}", headers=auth_headers_admin
    )
    assert resp.status_code == 200
    data = UserOut.model_validate(resp.json())
    assert data.id == user_in_db.id


@pytest.mark.anyio
async def test_get_user_unauthorized(
    async_client: AsyncClient, user_in_db: User, auth_headers_user: dict[str, str]
):
    resp = await async_client.get(
        f"/auth/users/{user_in_db.id}", headers=auth_headers_user
    )
    assert resp.status_code == 403


@pytest.mark.anyio
async def test_register_admin_authorized(async_client: AsyncClient, auth_headers_admin):
    email = "admin2@test.com"
    name = "admin2"
    payload = RegisterIn(
        email=email,
        password=PASSWORD,
        name=name,
        username=name,
        phone="0612345678",
        active=True,
        birth_year=1990,
    )
    resp = await async_client.post(
        "/auth/register_admin",
        json=payload.model_dump(mode="json"),
        headers=auth_headers_admin,
    )
    assert resp.status_code == 201
    data = RegisterOut.model_validate(resp.json())
    assert data.email == email
    assert data.name == name
    assert data.id is not None


@pytest.mark.anyio
async def test_register_admin_unauthorized(
    async_client: AsyncClient, auth_headers_user
):
    email = "admin3@test.com"
    name = "admin3"
    payload = RegisterIn(
        email=email,
        password=PASSWORD,
        name=name,
        username=name,
        phone="0612345678",
        active=True,
        birth_year=1990,
    )
    resp = await async_client.post(
        "/auth/register_admin",
        json=payload.model_dump(mode="json"),
        headers=auth_headers_user,
    )
    assert resp.status_code == 403
