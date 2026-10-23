from datetime import UTC, datetime, timedelta

import jwt
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash
from pwdlib.exceptions import UnknownHashError

from app.core.config import settings

_password_hash = PasswordHash.recommended()
_dummy_password_hash = _password_hash.hash("taskhub-nonexistent-user-password")
_JWT_ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return _password_hash.hash(password)


def verify_password(password: str, password_hash: str | None) -> bool:
    encoded_hash = password_hash or _dummy_password_hash
    try:
        password_matches = _password_hash.verify(password, encoded_hash)
    except UnknownHashError:
        return False
    return password_matches and password_hash is not None


def create_access_token(user_id: int) -> str:
    now = datetime.now(UTC)
    claims = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
    }
    return jwt.encode(
        claims,
        settings.jwt_secret_key.get_secret_value(),
        algorithm=_JWT_ALGORITHM,
    )


def decode_access_token(token: str) -> int | None:
    try:
        claims = jwt.decode(
            token,
            settings.jwt_secret_key.get_secret_value(),
            algorithms=[_JWT_ALGORITHM],
            options={"require": ["exp", "iat", "sub"]},
        )
    except InvalidTokenError:
        return None

    subject = claims.get("sub")
    if not isinstance(subject, str) or not subject.isdecimal():
        return None
    return int(subject)
