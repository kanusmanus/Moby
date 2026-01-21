from pydantic import BaseModel
import os


class Settings(BaseModel):
    app_name: str = os.getenv("APP_NAME", "Parking API")
    env: str = os.getenv("APP_ENV", "dev")
    host: str = os.getenv("APP_HOST", "0.0.0.0")
    port: int = int(os.getenv("APP_PORT", 8000))

    jwt_secret: str = os.getenv("JWT_SECRET", "changeme")
    jwt_alg: str = os.getenv("JWT_ALG", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

    database_url: str = os.getenv(
        "DATABASE_URL", "postgresql+asyncpg://app:app_pw@db:5432/parking"
    )
    sync_database_url: str = os.getenv(
        "SYNC_DATABASE_URL", "postgresql://app:app_pw@db:5432/parking"
    )
    redis_url: str = os.getenv("REDIS_URL", "redis://redis:6379/0")


settings = Settings()

