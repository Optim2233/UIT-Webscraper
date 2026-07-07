"""Redis-backed content-hash state used to detect updated lecture files."""

from __future__ import annotations

import redis

import config


class HashStore:
    def __init__(self, redis_url: str = config.REDIS_URL, namespace: str = config.REDIS_NAMESPACE):
        self.namespace = namespace.rstrip(":")
        self.redis = redis.Redis.from_url(redis_url, decode_responses=True)

    def _key(self, identity: str) -> str:
        return f"{self.namespace}:{identity}"

    def ping(self) -> bool:
        return bool(self.redis.ping())

    def get(self, identity: str) -> str | None:
        return self.redis.get(self._key(identity))

    def set(self, identity: str, digest: str) -> None:
        self.redis.set(self._key(identity), digest)

    def is_new_or_changed(self, identity: str, digest: str) -> bool:
        existing = self.get(identity)
        return existing != digest
