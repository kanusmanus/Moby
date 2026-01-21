from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_session

from app.schemas.parking_session import ParkingSessionOut
from app.services.auth import require_roles
from app.services.parking_sessions import (
    retrieve_parking_session,
)


router = APIRouter()


@router.get(
    "/{parking_session_id}",
    response_model=ParkingSessionOut,
    status_code=status.HTTP_200_OK,
)
async def get_parking_session(
    parking_session_id: int,
    db: AsyncSession = Depends(get_session),
    current_user=Depends(require_roles("admin")),
):
    session = await retrieve_parking_session(db, parking_session_id)
    return ParkingSessionOut.model_validate(session)
