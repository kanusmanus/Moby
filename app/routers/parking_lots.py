from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_session

from app.models.user import User
from app.schemas.parking_lot import ParkingLotIn, ParkingLotOut
from app.services.auth import get_current_user, require_roles
from app.services.parking_lots import (
    create_parking_lot,
    delete_parking_lot,
    retrieve_parking_lot,
    update_parking_lot,
)


router = APIRouter()


@router.get(
    "/{parking_lot_id}",
    response_model=ParkingLotOut,
    status_code=status.HTTP_200_OK,
)
async def get_parking_lot(
    parking_lot_id: int,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    parking_lot = await retrieve_parking_lot(db, parking_lot_id)
    return ParkingLotOut.model_validate(parking_lot)


@router.post("", response_model=ParkingLotOut, status_code=status.HTTP_201_CREATED)
async def add_parking_lot(
    payload: ParkingLotIn,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_roles("admin", "hotel_manager")),
):
    new_parking_lot = await create_parking_lot(db, payload)
    return ParkingLotOut.model_validate(new_parking_lot)


@router.put(
    "/{parking_lot_id}", response_model=ParkingLotOut, status_code=status.HTTP_200_OK
)
async def update_lot(
    parking_lot_id: int,
    payload: ParkingLotIn,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_roles("admin", "hotel_manager")),
):
    updated = await update_parking_lot(db, parking_lot_id, payload, current_user)
    return ParkingLotOut.model_validate(updated)


@router.delete("/{parking_lot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lot(
    parking_lot_id: int,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_roles("admin", "hotel_manager")),
):
    await delete_parking_lot(db, parking_lot_id, current_user)
