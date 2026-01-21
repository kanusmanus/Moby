from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.models.vehicle import Vehicle
from app.models.user import User
from app.schemas.vehicle import VehicleIn


async def create_vehicle(
    db: AsyncSession, payload: VehicleIn, current_user: User
) -> Vehicle:
    """Create a new vehicle for the current user."""

    # Check if license plate already exists
    result = await db.execute(
        select(Vehicle).where(Vehicle.license_plate == payload.license_plate)
    )
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=409, detail="Vehicle with this license plate already exists"
        )

    # Create vehicle for current user
    vehicle = Vehicle(
        user_id=current_user.id,
        license_plate=payload.license_plate,
        make=payload.make,
        model=payload.model,
        color=payload.color,
        year=payload.year,
    )

    db.add(vehicle)
    await db.commit()
    await db.refresh(vehicle)

    return vehicle


async def get_user_vehicles(db: AsyncSession, current_user: User) -> list[Vehicle]:
    """Get all vehicles for the current user."""
    result = await db.execute(select(Vehicle).where(Vehicle.user_id == current_user.id))
    return list(result.scalars().all())


async def get_vehicle(db: AsyncSession, vehicle_id: int, current_user: User) -> Vehicle:
    """Get a specific vehicle."""
    vehicle = await db.get(Vehicle, vehicle_id)

    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    # Users can only see their own vehicles (unless admin)
    if current_user.role != "admin" and vehicle.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    return vehicle


async def update_vehicle(
    db: AsyncSession, vehicle_id: int, payload: VehicleIn, current_user: User
) -> Vehicle:
    """Update a vehicle."""
    vehicle = await get_vehicle(db, vehicle_id, current_user)

    # Check if new license plate conflicts with another vehicle
    if payload.license_plate != vehicle.license_plate:
        result = await db.execute(
            select(Vehicle).where(Vehicle.license_plate == payload.license_plate)
        )
        existing = result.scalar_one_or_none()
        if existing:
            raise HTTPException(
                status_code=409, detail="Vehicle with this license plate already exists"
            )

    # Update fields
    vehicle.license_plate = payload.license_plate
    vehicle.make = payload.make
    vehicle.model = payload.model
    vehicle.color = payload.color
    vehicle.year = payload.year

    await db.commit()
    await db.refresh(vehicle)

    return vehicle


async def delete_vehicle(db: AsyncSession, vehicle_id: int, current_user: User) -> None:
    """Delete a vehicle."""
    vehicle = await get_vehicle(db, vehicle_id, current_user)

    await db.delete(vehicle)
    await db.commit()

