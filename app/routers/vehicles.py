from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.models.user import User
from app.schemas.vehicle import VehicleIn, VehicleOut
from app.services.auth import get_current_user
from app.services.vehicles import (
    create_vehicle,
    get_user_vehicles,
    get_vehicle,
    update_vehicle,
    delete_vehicle,
)

router = APIRouter()


@router.get("", response_model=list[VehicleOut])
async def list_my_vehicles(
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get all vehicles for the current user."""
    vehicles = await get_user_vehicles(db, current_user)
    return vehicles


@router.post("", response_model=VehicleOut, status_code=status.HTTP_201_CREATED)
async def add_vehicle(
    payload: VehicleIn,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Create a new vehicle."""
    vehicle = await create_vehicle(db, payload, current_user)
    return VehicleOut.model_validate(vehicle)


@router.get("/{vehicle_id}", response_model=VehicleOut)
async def get_vehicle_by_id(
    vehicle_id: int,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get a specific vehicle."""
    vehicle = await get_vehicle(db, vehicle_id, current_user)
    return VehicleOut.model_validate(vehicle)


@router.put("/{vehicle_id}", response_model=VehicleOut)
async def update_vehicle_by_id(
    vehicle_id: int,
    payload: VehicleIn,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Update a vehicle."""
    vehicle = await update_vehicle(db, vehicle_id, payload, current_user)
    return VehicleOut.model_validate(vehicle)


@router.delete("/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vehicle_by_id(
    vehicle_id: int,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Delete a vehicle."""
    await delete_vehicle(db, vehicle_id, current_user)

