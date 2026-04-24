import os
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_EXPIRE_MIN: int = 15
    REFRESH_EXPIRE_DAYS: int = 30

    REDIS_URL: str = "redis://localhost:16379/0"

    DEBUG: bool = True
    SERVICE_NAME: str = "wardrobe-service"

    MINIO_ENDPOINT: str | None = os.getenv("MINIO_ENDPOINT")
    MINIO_ACCESS_KEY: str | None = os.getenv("MINIO_ACCESS_KEY")
    MINIO_SECRET_KEY: str | None = os.getenv("MINIO_SECRET_KEY")
    MINIO_BUCKET: str | None = os.getenv("MINIO_BUCKET")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
