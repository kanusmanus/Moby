"""
tests/discounts_test.py

Pure unit tests for the discount service.

"""

from __future__ import annotations

from httpx import AsyncClient
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock

from app.models.discount_code import DiscountCode
from app.schemas.discounts import DiscountGenerateIn, DiscountOut
from app.services import discounts


# --------------------------
# Helpers
# --------------------------


def make_discount(
    code="WELCOME20",
    percent=20,
    enabled=True,
    uses_count=0,
):
    return DiscountCode(
        id=1,
        code=code,
        percent=percent,
        enabled=enabled,
        single_use=False,
        max_uses=None,
        uses_count=uses_count,
        valid_from=None,
        valid_until=None,
    )


# --------------------------
# calculate_discount
# --------------------------


@pytest.mark.anyio
async def test_calculate_discount_basic():
    assert discounts.calculate_discount(100.0, 20) == 20.0


@pytest.mark.anyio
async def test_calculate_discount_zero_or_negative():
    assert discounts.calculate_discount(0.0, 20) == 0.0
    assert discounts.calculate_discount(-10.0, 20) == 0.0


# --------------------------
# apply_discount (mocked DB)
# --------------------------


@pytest.mark.anyio
async def test_apply_discount_no_code():
    final_cost, discount_amount, code_id, dc = await discounts.apply_discount(
        db=AsyncMock(spec=AsyncSession),
        original_cost=50.0,
        discount_code_str=None,
    )

    assert final_cost == 50.0
    assert discount_amount == 0.0
    assert code_id is None
    assert dc is None


@pytest.mark.anyio
async def test_apply_discount_valid_code(monkeypatch):
    fake_discount = make_discount()

    # Mock DB lookup
    monkeypatch.setattr(
        discounts,
        "get_discount_by_code",
        AsyncMock(return_value=fake_discount),
    )

    # Validation should pass
    monkeypatch.setattr(
        discounts,
        "validate_discount_code",
        AsyncMock(return_value=None),
    )

    final_cost, discount_amount, code_id, dc = await discounts.apply_discount(
        db=AsyncMock(spec=AsyncSession),
        original_cost=100.0,
        discount_code_str="WELCOME20",
    )

    assert discount_amount == 20.0
    assert final_cost == 80.0
    assert code_id == 1
    assert dc is not None
    assert dc.code == "WELCOME20"


@pytest.mark.anyio
async def test_generate_discounts_authorized_admin(
    async_client: AsyncClient,
    auth_headers_admin: dict[str, str],
):
    payload = DiscountGenerateIn(
        count=3,
        prefix="TEST",
        percent=15,
        enabled=True,
        description="pytest generated",
        single_use=True,
        max_uses=1,
    )

    resp = await async_client.post(
        "/discounts/generate",
        json=payload.model_dump(mode="json"),
        headers=auth_headers_admin,
    )

    assert resp.status_code == 200
    data = [DiscountOut.model_validate(x) for x in resp.json()]
    assert len(data) == 3

    # Basic field checks + uniqueness
    codes = [d.code for d in data]
    assert len(set(codes)) == 3

    for d in data:
        assert d.code.startswith("TEST")
        assert d.percent == 15
        assert d.enabled is True
        assert d.description == "pytest generated"
        assert d.single_use is True
        assert d.max_uses == 1


@pytest.mark.anyio
async def test_generate_discounts_authorized_hotel_manager(
    async_client: AsyncClient,
    auth_headers_hotel_manager: dict[str, str],
):
    payload = DiscountGenerateIn(
        count=2,
        prefix="HM",
        percent=10,
        enabled=False,
        description="hotel manager batch",
        single_use=False,
        max_uses=10,
    )

    resp = await async_client.post(
        "/discounts/generate",
        json=payload.model_dump(mode="json"),
        headers=auth_headers_hotel_manager,
    )

    assert resp.status_code == 200
    data = [DiscountOut.model_validate(x) for x in resp.json()]
    assert len(data) == 2

    codes = [d.code for d in data]
    assert len(set(codes)) == 2
    for d in data:
        assert d.code.startswith("HM")
        assert d.percent == 10
        assert d.enabled is False
        assert d.description == "hotel manager batch"
        assert d.single_use is False
        assert d.max_uses == 10


@pytest.mark.anyio
async def test_generate_discounts_unauthorized_user(
    async_client: AsyncClient,
    auth_headers_user: dict[str, str],
):
    payload = DiscountGenerateIn(
        count=1,
        prefix="NO",
        percent=5,
        enabled=True,
        description="should fail",
        single_use=True,
        max_uses=1,
    )

    resp = await async_client.post(
        "/discounts/generate",
        json=payload.model_dump(mode="json"),
        headers=auth_headers_user,
    )

    assert resp.status_code == 403


@pytest.mark.anyio
async def test_generate_discounts_requires_auth(async_client: AsyncClient):
    payload = DiscountGenerateIn(
        count=1,
        prefix="NOAUTH",
        percent=5,
        enabled=True,
        description="no auth",
        single_use=True,
        max_uses=1,
    )

    resp = await async_client.post(
        "/discounts/generate",
        json=payload.model_dump(mode="json"),
    )

    assert resp.status_code in (401, 403)


@pytest.mark.anyio
async def test_generate_discounts_persists_and_no_collisions_across_calls(
    async_client: AsyncClient,
    auth_headers_admin: dict[str, str],
):
    payload = DiscountGenerateIn(
        count=5,
        prefix="COL",
        percent=20,
        enabled=True,
        description="collision check",
        single_use=False,
        max_uses=99,
    )

    r1 = await async_client.post(
        "/discounts/generate",
        json=payload.model_dump(mode="json"),
        headers=auth_headers_admin,
    )
    assert r1.status_code == 200
    d1 = [DiscountOut.model_validate(x) for x in r1.json()]

    r2 = await async_client.post(
        "/discounts/generate",
        json=payload.model_dump(mode="json"),
        headers=auth_headers_admin,
    )
    assert r2.status_code == 200
    d2 = [DiscountOut.model_validate(x) for x in r2.json()]

    codes1 = {d.code.lower() for d in d1}
    codes2 = {d.code.lower() for d in d2}

    assert len(d1) == 5
    assert len(d2) == 5
    assert codes1.isdisjoint(codes2)  # no overlap between batches
