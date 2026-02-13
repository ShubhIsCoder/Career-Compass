from __future__ import annotations

import json

import redis
from redis import Redis

from app.config import settings


class RedisStore:
    def __init__(self) -> None:
        self.client: Redis = redis.from_url(settings.redis_url, decode_responses=True)

    def ping(self) -> bool:
        return bool(self.client.ping())

    def incr_with_ttl(self, key: str, ttl_seconds: int) -> int:
        value = self.client.incr(key)
        if value == 1:
            self.client.expire(key, ttl_seconds)
        return int(value)

    def set_json(self, key: str, payload: dict, ttl_seconds: int = 3600) -> None:
        self.client.setex(key, ttl_seconds, json.dumps(payload))

    def get_json(self, key: str) -> dict | None:
        raw = self.client.get(key)
        return json.loads(raw) if raw else None
