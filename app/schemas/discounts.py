from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class DiscountCreate(BaseModel):
    code: str = Field(..., min_length=2, max_length=50)
    percent: int = Field(..., ge=0, le=100)
    enabled: bool = True
    description: Optional[str] = None
    single_use: bool = False
    max_uses: Optional[int] = Field(default=None, ge=1)
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None


class DiscountUpdate(BaseModel):
    percent: Optional[int] = Field(default=None, ge=0, le=100)
    enabled: Optional[bool] = None
    description: Optional[str] = None
    single_use: Optional[bool] = None
    max_uses: Optional[int] = Field(default=None, ge=1)
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None


class DiscountOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    percent: int
    enabled: bool
    description: Optional[str] = None
    single_use: bool
    max_uses: Optional[int] = None
    uses_count: int
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None


class DiscountGenerateIn(BaseModel):
    percent: int = Field(..., ge=0, le=100)
    count: int = Field(default=10, ge=1, le=500)
    prefix: str = ""
    enabled: bool = True
    single_use: bool = True
    max_uses: Optional[int] = Field(default=None, ge=1)
    description: Optional[str] = None


class DiscountValidateOut(BaseModel):
    valid: bool
    code: str
    percent: Optional[int] = None
    message: Optional[str] = None
