from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_session
from app.models.user import User
from app.schemas.payment import PaymentIn, PaymentOut
from app.services.auth import require_roles
from app.services.payments import handle_payment, retrieve_payment


router = APIRouter()


@router.get(
    "/{payment_id}",
    response_model=PaymentOut,
    status_code=status.HTTP_200_OK,
)
async def get_payment(
    payment_id: int,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_roles("admin")),
):
    payment = await retrieve_payment(db, payment_id, current_user)
    return PaymentOut.model_validate(payment)


@router.post("/pay", response_model=PaymentOut, status_code=status.HTTP_200_OK)
async def pay_payment(
    payload: PaymentIn,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_roles("parking_meter")),
):
    payment = await handle_payment(db, payload, current_user)
    return PaymentOut.model_validate(payment)
