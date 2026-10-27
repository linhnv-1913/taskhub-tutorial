import os
import time
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from redis import Redis
from sqlalchemy import event
from sqlalchemy.orm import sessionmaker

from app.core.constants import TAG_CACHE_KEY_PREFIX
from app.core.enums import UserRole
from app.models.tag import Tag
from app.models.user import User
from app.services import tag_cache
from tests.helpers import register_and_login


@pytest.fixture
def redis_cache(monkeypatch):
    url = os.environ.get("TASKHUB_TEST_REDIS_URL")
    if not url:
        pytest.skip("Set TASKHUB_TEST_REDIS_URL to an isolated Redis database")
    redis = Redis.from_url(url, decode_responses=True)
    redis.ping()
    version_key = f"taskhub:test:tags:version:{uuid4().hex}"
    monkeypatch.setattr(tag_cache, "TAG_CACHE_VERSION_KEY", version_key)
    monkeypatch.setattr(tag_cache.settings, "redis_url", url)
    monkeypatch.setattr(tag_cache.settings, "tag_cache_ttl_seconds", 30)
    versions = []
    yield redis, version_key, versions
    current = redis.get(version_key)
    if current:
        versions.append(current)
    for version in versions:
        for key in redis.scan_iter(f"{TAG_CACHE_KEY_PREFIX}:{version}:*"):
            redis.delete(key)
    redis.delete(version_key)
    redis.close()


def test_cache_pages_invalidation_and_permissions(
    client: TestClient, db_session_factory: sessionmaker, redis_cache
) -> None:
    redis, version_key, versions = redis_cache
    admin, headers = register_and_login(client, "tags-admin")
    _, user_headers = register_and_login(client, "tags-user")
    with db_session_factory() as db:
        db.get(User, admin["id"]).role = UserRole.ADMIN
        db.add_all([Tag(name="Alpha"), Tag(name="Beta")])
        db.commit()

    calls = []

    def count_tag_queries(_conn, _cursor, statement, _parameters, _context, _many):
        if "FROM tags" in statement:
            calls.append(statement)

    engine = db_session_factory.kw["bind"]
    event.listen(engine, "before_cursor_execute", count_tag_queries)
    try:
        assert client.get("/api/tags").status_code == 401
        first = client.get("/api/tags?skip=0&limit=1", headers=headers)
        assert first.json()["total"] == 2
        assert first.json()["items"][0]["name"] == "Alpha"
        before = len(calls)
        assert client.get("/api/tags?skip=0&limit=1", headers=headers).json() == first.json()
        assert len(calls) == before
        second = client.get("/api/tags?skip=1&limit=1", headers=headers)
        assert second.json()["items"][0]["name"] == "Beta"
        assert len(calls) > before
        version = redis.get(version_key)
        versions.append(version)
        assert client.get("/api/tags?skip=0&limit=1").status_code == 401
        assert 0 < redis.ttl(f"taskhub:tags:{version}:0:1") <= 30
        assert client.post("/api/tags", headers=user_headers, json={"name": "Gamma"}).status_code == 403
        assert client.post("/api/tags", headers=headers, json={"name": "Alpha"}).status_code == 409
        assert redis.get(version_key) == version
        assert client.post("/api/tags", headers=headers, json={"name": "Gamma"}).status_code == 201
        assert redis.get(version_key) != version
        # A reader finishing after invalidation may only populate the old version.
        redis.set(f"taskhub:tags:{version}:0:1", first.text, ex=30)
        assert client.get("/api/tags?skip=0&limit=1", headers=headers).json()["total"] == 3
        assert client.get("/api/tags?skip=1&limit=1", headers=headers).json()["total"] == 3
    finally:
        event.remove(engine, "before_cursor_execute", count_tag_queries)


def test_invalid_cache_and_unavailable_redis_fall_back_to_database(
    client: TestClient, db_session_factory: sessionmaker, redis_cache, monkeypatch
) -> None:
    redis, version_key, versions = redis_cache
    admin, headers = register_and_login(client, "cache-fallback-admin")
    with db_session_factory() as db:
        db.get(User, admin["id"]).role = UserRole.ADMIN
        db.add(Tag(name="Stored"))
        db.commit()
    assert client.get("/api/tags", headers=headers).json()["total"] == 1
    version = redis.get(version_key)
    versions.append(version)
    redis.set(f"taskhub:tags:{version}:0:20", "not-json", ex=30)
    assert client.get("/api/tags", headers=headers).json()["total"] == 1
    monkeypatch.setattr(tag_cache.settings, "redis_url", "redis://127.0.0.1:1/0")
    assert client.get("/api/tags", headers=headers).json()["total"] == 1
    assert client.post("/api/tags", headers=headers, json={"name": "Created"}).status_code == 201
    assert client.get("/api/tags", headers=headers).json()["total"] == 2


def test_failed_invalidation_is_bounded_by_ttl(
    client: TestClient, db_session_factory: sessionmaker, redis_cache, monkeypatch
) -> None:
    redis, version_key, versions = redis_cache
    admin, headers = register_and_login(client, "cache-expiry-admin")
    with db_session_factory() as db:
        db.get(User, admin["id"]).role = UserRole.ADMIN
        db.add(Tag(name="Original"))
        db.commit()
    url = tag_cache.settings.redis_url
    monkeypatch.setattr(tag_cache.settings, "tag_cache_ttl_seconds", 3)
    assert client.get("/api/tags", headers=headers).json()["total"] == 1
    versions.append(redis.get(version_key))
    monkeypatch.setattr(tag_cache.settings, "redis_url", "redis://127.0.0.1:1/0")
    assert client.post("/api/tags", headers=headers, json={"name": "New"}).status_code == 201
    monkeypatch.setattr(tag_cache.settings, "redis_url", url)
    assert client.get("/api/tags", headers=headers).json()["total"] == 1
    time.sleep(3.1)
    assert client.get("/api/tags", headers=headers).json()["total"] == 2


def test_invalid_redis_configuration_falls_back_without_redis(
    client: TestClient, db_session_factory: sessionmaker, monkeypatch
) -> None:
    admin, headers = register_and_login(client, "cache-no-redis-admin")
    with db_session_factory() as db:
        db.get(User, admin["id"]).role = UserRole.ADMIN
        db.commit()
    monkeypatch.setattr(tag_cache.settings, "redis_url", "invalid://redis")
    assert client.get("/api/tags", headers=headers).json()["total"] == 0
    assert client.post("/api/tags", headers=headers, json={"name": "Tag"}).status_code == 201
    assert client.get("/api/tags", headers=headers).json()["total"] == 1
