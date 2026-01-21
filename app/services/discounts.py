from typing import Optional, Tuple
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
from fastapi import HTTPException

from app.models.discount_code import DiscountCode
from app.models.discount_redemption import DiscountRedemption
from app.models.reservation import Reservation


def calculate_discount(original_cost: float, percent: int) -> float:
    """Calculate discount amount."""
    if original_cost <= 0:
        return 0.0
    return (percent / 100.0) * original_cost


async def get_discount_by_code(db: AsyncSession, code: str) -> DiscountCode:
    """Get discount code by code string (case-insensitive)."""
    result = await db.execute(
        select(DiscountCode).where(func.lower(DiscountCode.code) == code.lower())
    )
    dc = result.scalar_one_or_none()

    if not dc:
        raise HTTPException(status_code=404, detail="Discount code not found")

    return dc


async def validate_discount_code(db: AsyncSession, dc: DiscountCode) -> None:
    """Validate that a discount code can be used."""

    # Check if enabled
    if not dc.enabled:
        raise HTTPException(status_code=400, detail="Discount code is disabled")

    # Check validity dates
    now = datetime.now(timezone.utc)

    if dc.valid_from and now < dc.valid_from:
        raise HTTPException(status_code=400, detail="Discount code not yet valid")

    if dc.valid_until and now > dc.valid_until:
        raise HTTPException(status_code=400, detail="Discount code has expired")

    # Check usage limits
    if dc.single_use and dc.uses_count >= 1:
        raise HTTPException(status_code=400, detail="Discount code already used")

    if dc.max_uses and dc.uses_count >= dc.max_uses:
        raise HTTPException(status_code=400, detail="Discount code usage limit reached")


async def apply_discount(
    db: AsyncSession,
    original_cost: float,
    discount_code_str: Optional[str] = None,
) -> Tuple[float, float, Optional[int], Optional[DiscountCode]]:
    """
    Apply discount to cost.

    Returns: (final_cost, discount_amount, discount_code_id, discount_code_object)
    """
    if not discount_code_str:
        return original_cost, 0.0, None, None

    try:
        dc = await get_discount_by_code(db, discount_code_str)
        await validate_discount_code(db, dc)

        discount_amount = calculate_discount(original_cost, dc.percent)
        final_cost = original_cost - discount_amount

        return final_cost, discount_amount, dc.id, dc
    except HTTPException:
        # If discount is invalid, just return original cost
        return original_cost, 0.0, None, None


async def record_discount_redemption(
    db: AsyncSession,
    discount_code: DiscountCode,
    user_id: int,
    reservation: Reservation,
):
    """Record that a discount code was used."""
    redemption = DiscountRedemption(
        discount_code_id=discount_code.id,
        user_id=user_id,
        reservation_id=reservation.id,
    )
    db.add(redemption)

    # Increment usage counter
    discount_code.uses_count += 1

