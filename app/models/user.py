import enum
from typing import TYPE_CHECKING
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Enum, String, Boolean
from app.db.base import Base, TimestampMixin

# --- help linters : circular-safe imports ---
if TYPE_CHECKING:
    from app.models.reservation import Reservation
    from app.models.vehicle import Vehicle
    from app.models.payment import Payment


class UserRole(str, enum.Enum):
    user = "user"
    admin = "admin"
    hotel_manager = "hotel_manager"
    parking_meter = "parking_meter"


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(100))
    password_hash: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    phone: Mapped[str] = mapped_column(String(15))
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role"),
        nullable=False,
        default=UserRole.user,
    )

    active: Mapped[bool] = mapped_column(Boolean, default=True)
    birth_year: Mapped[int] = mapped_column()

    reservations: Mapped[list["Reservation"]] = relationship(
        back_populates="user",
        passive_deletes=True,
    )
    vehicles: Mapped[list["Vehicle"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    payments: Mapped[list["Payment"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
