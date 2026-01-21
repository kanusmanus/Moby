from datetime import datetime
from sqlalchemy import Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class DiscountRedemption(Base):
    __tablename__ = "discount_redemptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    discount_code_id: Mapped[int] = mapped_column(
        ForeignKey("discount_codes.id", ondelete="CASCADE"), index=True, nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    reservation_id: Mapped[int] = mapped_column(
        ForeignKey("reservations.id", ondelete="CASCADE"), index=True, nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    discount_code = relationship("DiscountCode", back_populates="redemptions")
