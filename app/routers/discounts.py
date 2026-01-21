import secrets
import string
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.session import get_session
from app.models.discount_code import DiscountCode
from app.models.user import User
from app.schemas.discounts import (
    DiscountCreate,
    DiscountUpdate,
    DiscountOut,
    DiscountGenerateIn,
)


from app.schemas.discounts import DiscountValidateOut
from app.services.auth import get_current_user, require_roles
from app.services.discounts import get_discount_by_code, validate_discount_code


router = APIRouter()


def _gen_code(prefix: str = "", length: int = 8) -> str:
    alphabet = string.ascii_uppercase + string.digits
    return prefix + "".join(secrets.choice(alphabet) for _ in range(length))


@router.get("", response_model=list[DiscountOut])
async def list_discounts(
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_roles("admin")),
):
    res = await db.execute(select(DiscountCode).order_by(DiscountCode.id.desc()))
    return res.scalars().all()


@router.post(
    "",
    response_model=DiscountOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_discount(
    payload: DiscountCreate,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_roles("admin", "hotel_manager")),
):
    # case-insensitive uniqueness check
    existing = await db.execute(
        select(DiscountCode).where(
            func.lower(DiscountCode.code) == payload.code.lower()
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Discount code already exists")

    dc = DiscountCode(**payload.model_dump())
    db.add(dc)
    await db.commit()
    await db.refresh(dc)
    return dc


@router.patch("/{discount_id}", response_model=DiscountOut)
async def update_discount(
    discount_id: int,
    payload: DiscountUpdate,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_roles("admin", "hotel_manager")),
):
    res = await db.execute(select(DiscountCode).where(DiscountCode.id == discount_id))
    dc = res.scalar_one_or_none()
    if not dc:
        raise HTTPException(status_code=404, detail="Discount code not found")

    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(dc, k, v)

    await db.commit()
    await db.refresh(dc)
    return dc


@router.post("/generate", response_model=list[DiscountOut])
async def generate_discounts(
    payload: DiscountGenerateIn,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_roles("admin", "hotel_manager")),
):
    created: list[DiscountCode] = []

    for _ in range(payload.count):
        # avoid collisions by retrying a few times
        for _try in range(5):
            code = _gen_code(prefix=payload.prefix)
            exists_res = await db.execute(
                select(DiscountCode.id).where(
                    func.lower(DiscountCode.code) == code.lower()
                )
            )
            if not exists_res.scalar_one_or_none():
                break
        else:
            raise HTTPException(
                status_code=500, detail="Failed to generate unique code"
            )

        dc = DiscountCode(
            code=code,
            percent=payload.percent,
            enabled=payload.enabled,
            description=payload.description,
            single_use=payload.single_use,
            max_uses=payload.max_uses,
        )
        db.add(dc)
        created.append(dc)

    await db.commit()
    for dc in created:
        await db.refresh(dc)
    return created


@router.get("/validate/{code}", response_model=DiscountValidateOut)
async def validate_discount_code_public(
    code: str,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        dc = await get_discount_by_code(db, code)
        await validate_discount_code(db, dc)

        return DiscountValidateOut(
            valid=True,
            code=dc.code,
            percent=dc.percent,
        )

    except HTTPException as e:
        return DiscountValidateOut(
            valid=False,
            code=code,
            message=str(e.detail),
        )
