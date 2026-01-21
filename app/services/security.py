from passlib.hash import argon2


def hash_password(plain: str) -> str:
    return argon2.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return argon2.verify(plain, hashed)


def needs_update(hashed: str) -> bool:
    return argon2.needs_update(hashed)
