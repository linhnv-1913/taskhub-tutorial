from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from pydantic import EmailStr, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url

from app.core import messages
from app.core.constants import (
    DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES,
    DEFAULT_SMTP_PORT,
    DEFAULT_SMTP_TIMEOUT_SECONDS,
    DEFAULT_TAG_CACHE_TTL_SECONDS,
    JWT_SECRET_KEY_MIN_LENGTH,
    MAX_ACCESS_TOKEN_EXPIRE_MINUTES,
    MAX_SMTP_PORT,
    MAX_SMTP_TIMEOUT_SECONDS,
    MAX_TAG_CACHE_TTL_SECONDS,
    MIN_ACCESS_TOKEN_EXPIRE_MINUTES,
    MIN_SMTP_PORT,
    MIN_SMTP_TIMEOUT_SECONDS_EXCLUSIVE,
    MIN_TAG_CACHE_TTL_SECONDS,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE_URL = f"sqlite:///{(PROJECT_ROOT / 'taskhub.db').as_posix()}"


def _normalize_database_url(url: str) -> str:
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    elif url.startswith("mysql://"):
        url = url.replace("mysql://", "mysql+pymysql://", 1)

    database_url = make_url(url)
    if (
        database_url.get_backend_name() == "sqlite"
        and database_url.database not in {None, "", ":memory:"}
    ):
        database_path = Path(database_url.database)
        if not database_path.is_absolute():
            database_url = database_url.set(
                database=(PROJECT_ROOT / database_path).resolve().as_posix()
            )

    return database_url.render_as_string(hide_password=False)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = DEFAULT_DATABASE_URL
    jwt_secret_key: SecretStr
    access_token_expire_minutes: int = Field(
        default=DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES,
        ge=MIN_ACCESS_TOKEN_EXPIRE_MINUTES,
        le=MAX_ACCESS_TOKEN_EXPIRE_MINUTES,
    )
    cors_allowed_origins: list[str] = Field(default_factory=list)
    log_level: Literal["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"] = "INFO"

    @field_validator("cors_allowed_origins")
    @classmethod
    def validate_cors_allowed_origins(cls, value: list[str]) -> list[str]:
        origins = [origin.strip() for origin in value]
        if "*" in origins:
            raise ValueError(messages.CORS_EXPLICIT_ORIGINS_REQUIRED)

        normalized: list[str] = []
        for origin in origins:
            parsed = urlsplit(origin)
            if (
                parsed.scheme not in {"http", "https"}
                or not parsed.netloc
                or parsed.username is not None
                or parsed.password is not None
                or parsed.path not in {"", "/"}
                or parsed.query
                or parsed.fragment
            ):
                raise ValueError(messages.CORS_HTTP_ORIGINS_REQUIRED)
            normalized.append(f"{parsed.scheme}://{parsed.netloc}")
        return normalized

    @field_validator("jwt_secret_key")
    @classmethod
    def validate_jwt_secret_key(cls, value: SecretStr) -> SecretStr:
        if len(value.get_secret_value()) < JWT_SECRET_KEY_MIN_LENGTH:
            raise ValueError(
                "JWT_SECRET_KEY must contain at least "
                f"{JWT_SECRET_KEY_MIN_LENGTH} characters"
            )
        return value

    smtp_host: str | None = None
    smtp_port: int = Field(
        default=DEFAULT_SMTP_PORT,
        ge=MIN_SMTP_PORT,
        le=MAX_SMTP_PORT,
    )
    smtp_from_email: EmailStr | None = None
    smtp_username: str | None = None
    smtp_password: SecretStr | None = None
    smtp_starttls: bool = True
    smtp_timeout_seconds: float = Field(
        default=DEFAULT_SMTP_TIMEOUT_SECONDS,
        gt=MIN_SMTP_TIMEOUT_SECONDS_EXCLUSIVE,
        le=MAX_SMTP_TIMEOUT_SECONDS,
    )
    redis_url: str | None = None
    tag_cache_ttl_seconds: int = Field(
        default=DEFAULT_TAG_CACHE_TTL_SECONDS,
        ge=MIN_TAG_CACHE_TTL_SECONDS,
        le=MAX_TAG_CACHE_TTL_SECONDS,
    )


settings = Settings()
DATABASE_URL = _normalize_database_url(settings.database_url)
