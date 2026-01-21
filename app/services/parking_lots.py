from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.parking_lot import ParkingLot
from app.models.user import User, UserRole
from app.schemas.parking_lot import ParkingLotCostIn, ParkingLotIn
from app.services.exceptions import AccessForbidden, ParkingLotNotFound


async def retrieve_parking_lot(db: AsyncSession, parking_lot_id: int):
    existing = await db.execute(
        select(ParkingLot).where(ParkingLot.id == parking_lot_id)
    )
    parking_lot = existing.scalar_one_or_none()

    if parking_lot is None:
        raise ParkingLotNotFound()
    return parking_lot


async def create_parking_lot(db: AsyncSession, payload: ParkingLotIn):
    # Create + persist
    new_parking_lot = ParkingLot(
        name=payload.name,
        location=payload.location,
        address=payload.address,
        capacity=payload.capacity,
        created_by=payload.created_by,
        reserved=payload.reserved,
        tariff=payload.tariff,
        daytariff=payload.daytariff,
        latitude=payload.latitude,
        longitude=payload.longitude,
    )

    db.add(new_parking_lot)
    await db.flush()  # get PK
    await db.commit()
    await db.refresh(new_parking_lot)
    return new_parking_lot


async def update_parking_lot(
    db: AsyncSession, parking_lot_id: int, payload: ParkingLotIn, current_user: User
) -> ParkingLot:
    parking_lot = await retrieve_parking_lot(db, parking_lot_id)

    if (
        current_user.role == UserRole.hotel_manager
        and current_user.id != parking_lot.created_by
    ):
        raise AccessForbidden()

    # Full replace using ParkingLotIn
    parking_lot.name = payload.name
    parking_lot.location = payload.location
    parking_lot.address = payload.address
    parking_lot.capacity = payload.capacity
    parking_lot.reserved = payload.reserved
    parking_lot.tariff = payload.tariff
    parking_lot.daytariff = payload.daytariff
    parking_lot.latitude = payload.latitude
    parking_lot.longitude = payload.longitude

    await db.commit()
    await db.refresh(parking_lot)
    return parking_lot


async def delete_parking_lot(
    db: AsyncSession, parking_lot_id: int, current_user: User
) -> None:
    parking_lot = await retrieve_parking_lot(db, parking_lot_id)
    if (
        current_user.role == UserRole.hotel_manager
        and current_user.id != parking_lot.created_by
    ):
        raise AccessForbidden()

    await db.delete(parking_lot)
    await db.commit()


async def get_parking_lot_cost(db: AsyncSession, payload: ParkingLotCostIn) -> float:
    existing = await db.execute(select(ParkingLot).where(ParkingLot.id == payload.id))
    parking_lot = existing.scalar_one_or_none()
    if parking_lot is None:
        raise ParkingLotNotFound()
    return (
        parking_lot.daytariff
        if payload.hours >= 6
        else parking_lot.tariff * payload.hours
    )
