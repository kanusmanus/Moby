from datetime import datetime
from sqlalchemy import String, Integer, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class DiscountCode(Base, TimestampMixin):
    __tablename__ = "discount_codes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # e.g. FIRST50, WELCOME20, MP20-AB12CD34
    code: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False
    )

    # 0..100
    percent: Mapped[int] = mapped_column(Integer, nullable=False)

    # enabled/disabled
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    description: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Usage type:
    # - True  => single-use (only 1 redemption globally)
    # - False => multi-use (can be redeemed multiple times, optionally limited by max_uses)
    single_use: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Optional total usage limit (global). Example: max_uses=100
    max_uses: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Counter to avoid counting redemptions every time
    uses_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Optional validity window
    valid_from: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    valid_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    redemptions = relationship("DiscountRedemption", back_populates="discount_code")
