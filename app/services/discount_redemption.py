from sqlalchemy.ext.asyncio import AsyncSession

from app.models.discount_code import DiscountCode
from app.models.discount_redemption import DiscountRedemption


async def redeem_discount_code(
    db: AsyncSession,
    dc: DiscountCode,
    user_id: int,
    reservation_id: int,
) -> None:
    # 1) create redemption record
    db.add(
        DiscountRedemption(
            discount_code_id=dc.id,
            user_id=user_id,
            reservation_id=reservation_id,
        )
    )

    # 2) increment counter
    dc.uses_count += 1
