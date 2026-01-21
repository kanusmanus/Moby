from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.user import User
from app.scripts.import_common import ImportContext, load_json, pick, commit_every


def import_users(db: Session, ctx: ImportContext, filename: str = "users.json") -> None:
    """
    Expected JSON item keys (flexible):
    - id / user_id
    - email
    - username, name, phone, role, active, birth_year
    - password_hash (or passwordHash / hashed_password)
    """
    items = load_json(filename)

    for i, item in enumerate(items, start=1):
        old_id = pick(item, "id", "user_id", "userId")
        email = pick(item, "email", "mail")
        if not email:
            raise ValueError(f"User missing email: {item}")

        user = db.query(User).filter(User.email == email).first()

        if not user:
            user = User(
                username=pick(item, "username", "user_name", default=""),
                password_hash=pick(
                    item,
                    "password_hash",
                    "passwordHash",
                    "hashed_password",
                    default="IMPORT_ONLY",
                ),
                name=pick(item, "name", "full_name", "fullName", default=""),
                email=email,
                phone=str(
                    pick(item, "phone", "phone_number", "phoneNumber", default="")
                ),
                role=pick(item, "role", default="user"),
                active=bool(pick(item, "active", default=True)),
                birth_year=int(pick(item, "birth_year", "birthYear", default=0) or 0),
            )
            db.add(user)
            db.flush()
        else:
            # update existing fields if empty
            if not user.username:
                user.username = pick(
                    item, "username", "user_name", default=user.username
                )
            if not user.name:
                user.name = pick(
                    item, "name", "full_name", "fullName", default=user.name
                )
            if not user.phone:
                user.phone = str(
                    pick(
                        item, "phone", "phone_number", "phoneNumber", default=user.phone
                    )
                )
            if not user.role:
                user.role = pick(item, "role", default=user.role)

        if old_id is not None:
            ctx.user_id_map[old_id] = user.id

        commit_every(db, i, chunk=500)

    db.commit()
