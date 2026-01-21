from fastapi import FastAPI
from starlette.responses import JSONResponse
from app.core.config import settings
from app.routers import (
    auth,
    parking_lots,
    parking_sessions,
    payments,
    reservations,
    gate,
    discounts,
    vehicles
)
from app.services.exceptions import (
    AccountAlreadyExists,
    InvalidCredentials,
    InvalidTimeRange,
    ParkingLotNotFound,
    ParkingLotAtCapacity,
    ReservationNotFound,
    ReservationOverlap,
    UserNotFound,
)


app = FastAPI(title=settings.app_name)


@app.get("/health")
async def health():
    return {"status": "ok"}


app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(reservations.router, prefix="/reservations", tags=["reservations"])
app.include_router(parking_lots.router, prefix="/parking_lots", tags=["parking_lots"])
app.include_router(discounts.router, prefix="/discounts", tags=["discounts"])
app.include_router(gate.router, prefix="/gate", tags=["gate"])
app.include_router(
    parking_sessions.router, prefix="/parking_sessions", tags=["parking_sessions"]
)
app.include_router(payments.router, prefix="/payments", tags=["payments"])
app.include_router(vehicles.router, prefix="/vehicles", tags=["vehicles"])

# Handle our exceptions
@app.exception_handler(ReservationOverlap)
async def reservation_overlap_handler(_, exc: ReservationOverlap):
    return JSONResponse(
        status_code=409,
        content={"detail": "Time slot overlaps an existing reservation"},
    )


@app.exception_handler(ReservationNotFound)
async def reservation_not_found_handler(_, exc: ReservationNotFound):
    return JSONResponse(
        status_code=404,
        content={"detail": "Reservation could not be found"},
    )


@app.exception_handler(InvalidTimeRange)
async def invalid_time_range_handler(_, exc):
    return JSONResponse(
        status_code=422,
        content={"detail": "end_time must be after start_time"},
    )


@app.exception_handler(ParkingLotNotFound)
async def parking_lot_not_found_handler(_, exc: ParkingLotNotFound):
    return JSONResponse(
        status_code=404,
        content={"detail": "Parking lot could not be found"},
    )

@app.exception_handler(ParkingLotAtCapacity)
async def parking_lot_at_capacity_handler(_, exc: ParkingLotAtCapacity):
    return JSONResponse(
        status_code=409,
        content={"detail": "Parking lot is at full capacity for the requested time period"},
    )


@app.exception_handler(AccountAlreadyExists)
async def account_already_exists_handler(_, exc: AccountAlreadyExists):
    return JSONResponse(
        status_code=409,
        content={"detail": "Account already exists"},
    )


@app.exception_handler(InvalidCredentials)
async def invalid_credentials_handler(_, exc: InvalidCredentials):
    return JSONResponse(
        status_code=401,
        content={"detail": "Invalid credentials"},
    )


@app.exception_handler(UserNotFound)
async def user_not_found_handler(_, exc: UserNotFound):
    return JSONResponse(
        status_code=404,
        content={"detail": "User not found"},
    )
