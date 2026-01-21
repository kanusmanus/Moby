from pydantic import BaseModel, EmailStr, constr


class RegisterIn(BaseModel):
    email: EmailStr
    password: constr(min_length=8)  # pyright: ignore[reportInvalidTypeForm]
    name: constr(min_length=3, max_length=100)  # pyright: ignore[reportInvalidTypeForm]
    username: constr(min_length=3)  # pyright: ignore[reportInvalidTypeForm]
    phone: constr(min_length=9)  # pyright: ignore[reportInvalidTypeForm]
    active: bool
    birth_year: int


class RegisterOut(BaseModel):
    id: int
    email: EmailStr
    name: str


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class LoginOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    email: str
    name: str
    phone: str


class UserUpdateIn(BaseModel):
    email: EmailStr
    name: constr(min_length=3, max_length=100)  # pyright: ignore[reportInvalidTypeForm]
    phone: constr(min_length=9)  # pyright: ignore[reportInvalidTypeForm]
