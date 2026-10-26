import logging

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.api.dependencies import SessionDep

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/health", tags=["health"], include_in_schema=False)
def check_health(session: SessionDep) -> dict[str, str]:
    try:
        session.execute(text("SELECT 1"))
    except SQLAlchemyError:
        logger.error("Database readiness probe failed")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service unavailable",
        ) from None
    return {"status": "ok"}
