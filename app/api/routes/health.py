import logging

from fastapi import APIRouter
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.api.dependencies import SessionDep
from app.core import messages
from app.core.exceptions import ServiceUnavailableError

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/health", include_in_schema=False)
def check_health(session: SessionDep) -> dict[str, str]:
    try:
        session.execute(text("SELECT 1"))
    except SQLAlchemyError:
        logger.exception(messages.DATABASE_READINESS_FAILED)
        raise ServiceUnavailableError(messages.SERVICE_UNAVAILABLE) from None
    return {"status": "ok"}
