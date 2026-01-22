from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_session
from app.models.user import User
from app.schemas.auth import (
    LoginIn,
    LoginOut,
    RegisterIn,
    RegisterOut,
    UserOut,
    UserUpdateIn,
)
from app.services.auth import (
    create_user,
    create_admin,
    delete_user,
    get_current_user,
    get_user,
    login_account,
    require_roles,
    update_user,
)


router = APIRouter()


@router.post(
    "/register", response_model=RegisterOut, status_code=status.HTTP_201_CREATED
)
async def register(payload: RegisterIn, db: AsyncSession = Depends(get_session)):
    user = await create_user(db, payload)
    return RegisterOut(id=user.id, email=user.email, name=user.name)


@router.post("/login", response_model=LoginOut, status_code=status.HTTP_200_OK)
async def login(payload: LoginIn, db: AsyncSession = Depends(get_session)):
    return await login_account(db, payload)


@router.get("/users/{user_id}", response_model=UserOut, status_code=status.HTTP_200_OK)
async def user(
    user_id: int,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_roles("admin")),
):
    user = await get_user(db, user_id)
    return UserOut.model_validate(user)


@router.put("/users/{user_id}", response_model=UserOut, status_code=status.HTTP_200_OK)
async def update_other_user(
    user_id: int,
    payload: UserUpdateIn,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_roles("admin")),
):
    user = await update_user(db, payload, current_user)
    return UserOut.model_validate(user)


@router.delete(
    "/users/{user_id}", response_model=UserOut, status_code=status.HTTP_200_OK
)
async def delete_other_user(
    user_id: int,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_roles("admin")),
):
    user = await delete_user(db, user_id)
    return UserOut.model_validate(user)


@router.get("/users/me", response_model=UserOut, status_code=status.HTTP_200_OK)
async def get_me(
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    user = await get_user(db, current_user.id)
    return UserOut.model_validate(user)


@router.put("/users/me", response_model=UserOut, status_code=status.HTTP_200_OK)
async def update_me(
    payload: UserUpdateIn,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    user = await update_user(
        db,
        payload,
        current_user,
    )
    return UserOut.model_validate(user)


@router.delete("/users/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_me(
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    await delete_user(db, current_user.id)


@router.post(
    "/register_admin",
    response_model=RegisterOut,
    status_code=status.HTTP_201_CREATED,
)
async def register_admin(
    payload: RegisterIn,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_roles("admin")),
):
    admin = await create_admin(db, payload)
    return RegisterOut(id=admin.id, email=admin.email, name=admin.name)
