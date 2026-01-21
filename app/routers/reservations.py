from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_session
from app.models.user import User
from app.schemas.reservations import ReservationIn, ReservationOut
from app.services.auth import get_current_user
from app.services.reservations import create_reservation, retrieve_reservation


router = APIRouter()


@router.get(
    "/{reservation_id}",
    response_model=ReservationOut,
    status_code=status.HTTP_200_OK,
)
async def get_reservation(
    reservation_id: int,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    reservation = await retrieve_reservation(db, reservation_id, current_user)
    return ReservationOut.model_validate(reservation)


@router.post("", response_model=ReservationOut, status_code=status.HTTP_201_CREATED)
async def add_reservation(
    payload: ReservationIn,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    # app.services.reservation.py
    new_res = await create_reservation(db, payload, current_user)
    return ReservationOut.model_validate(new_res)
