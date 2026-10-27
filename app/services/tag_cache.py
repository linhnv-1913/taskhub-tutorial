import logging
from functools import lru_cache
from uuid import uuid4

from pydantic import ValidationError
from redis import Redis
from redis.backoff import NoBackoff
from redis.exceptions import RedisError
from redis.retry import Retry
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.constants import (
    REDIS_TIMEOUT_SECONDS,
    TAG_CACHE_CLIENT_CACHE_SIZE,
    TAG_CACHE_FIRST_PAGE_OFFSET,
    TAG_CACHE_KEY_PREFIX,
    TAG_CACHE_RETRY_ATTEMPTS,
    TAG_CACHE_VERSION_KEY,
)
from app.crud.tags import list_tags
from app.schemas.common import PaginatedResponse, PaginationParams
from app.schemas.tag import TagRead

logger = logging.getLogger(__name__)


@lru_cache(maxsize=TAG_CACHE_CLIENT_CACHE_SIZE)
def _client(url: str) -> Redis:
    return Redis.from_url(
        url, decode_responses=True,
        socket_connect_timeout=REDIS_TIMEOUT_SECONDS,
        socket_timeout=REDIS_TIMEOUT_SECONDS,
        retry=Retry(NoBackoff(), TAG_CACHE_RETRY_ATTEMPTS),
    )


def _version(client: Redis) -> str:
    client.set(TAG_CACHE_VERSION_KEY, uuid4().hex, nx=True)
    version = client.get(TAG_CACHE_VERSION_KEY)
    if version is None:
        raise ValueError("Tag cache version disappeared")
    return version


def get_cached_tags(db: Session, pagination: PaginationParams) -> PaginatedResponse[TagRead]:
    client = None
    key = None
    if settings.redis_url:
        try:
            client = _client(settings.redis_url)
            version = _version(client)
            key = (
                f"{TAG_CACHE_KEY_PREFIX}:"
                f"{version}:{pagination.skip}:{pagination.limit}"
            )
            cached = client.get(key)
            if cached is not None:
                return PaginatedResponse[TagRead].model_validate_json(cached)
        except (RedisError, ValueError, ValidationError):
            logger.warning("Tag cache read failed; querying the database")
            client = None

    tags, total = list_tags(db, pagination)
    result = PaginatedResponse[TagRead](
        items=[TagRead.model_validate(tag) for tag in tags], total=total
    )
    if (
        client is not None
        and key is not None
        and (pagination.skip == TAG_CACHE_FIRST_PAGE_OFFSET or tags)
    ):
        try:
            client.set(key, result.model_dump_json(), ex=settings.tag_cache_ttl_seconds)
        except RedisError:
            logger.warning("Tag cache write failed")
    return result


def invalidate_tag_cache() -> None:
    if settings.redis_url:
        try:
            _client(settings.redis_url).set(
                TAG_CACHE_VERSION_KEY, uuid4().hex
            )
        except (RedisError, ValueError):
            logger.warning("Tag cache invalidation failed; entries expire by TTL")
