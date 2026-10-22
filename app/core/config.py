from pathlib import Path

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url

from app.core import constants

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
        default=constants.DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES,
        ge=1,
        le=constants.MAX_ACCESS_TOKEN_EXPIRE_MINUTES,
    )

    @field_validator("jwt_secret_key")
    @classmethod
    def validate_jwt_secret_key(cls, value: SecretStr) -> SecretStr:
        if len(value.get_secret_value()) < constants.JWT_SECRET_KEY_MIN_LENGTH:
            raise ValueError(
                "JWT_SECRET_KEY must contain at least "
                f"{constants.JWT_SECRET_KEY_MIN_LENGTH} characters"
            )
        return value


settings = Settings()
DATABASE_URL = _normalize_database_url(settings.database_url)
