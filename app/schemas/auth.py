from typing import Literal

from app.schemas.common import BaseSchema


class TokenResponse(BaseSchema):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
