import asyncio
import json
import os
import random
import time
from datetime import datetime
from types import SimpleNamespace

import redis.asyncio as redis

from app.utils.serializers import alchemy_obj_to_dict  # moved out of utils.py


class Cache:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, host=None, port=None):
        if hasattr(self, "_initialized"):
            return
        self._client = redis.Redis(
            host=host or os.environ.get("REDIS_HOST", "127.0.0.1"),
            port=int(port or os.environ.get("REDIS_PORT", 6379)),
            decode_responses=True,
        )
        self.LOCK_TTL = 10         # seconds to hold the lock
        self.POLL_INTERVAL = 0.05  # 50ms between polls
        self.POLL_TIMEOUT = 5      # max seconds to wait
        self._initialized = True

    @staticmethod
    def _to_ns(d: dict) -> SimpleNamespace:
        d = dict(d)
        if isinstance(d.get("expires_at"), str):
            d["expires_at"] = datetime.fromisoformat(d["expires_at"])
        return SimpleNamespace(**d)

    @property
    def redis_client(self):
        return self._client


    async def get(self, prefix, key) -> SimpleNamespace | None:
        data = await self._client.get(f"{prefix}:{key}")
        if data is None:
            return None
        return self._to_ns(json.loads(data))

    async def coalesce_cache(self, prefix, cache_key: str, fetch_fn, ttl: int = 300):
        cached = await self.get(prefix, cache_key)
        if cached is not None:
            return cached

        lock_key = f"lock:{prefix}:{cache_key}"
        acquired = await self._client.set(lock_key, "1", nx=True, ex=self.LOCK_TTL)

        if acquired:
            try:
                data = alchemy_obj_to_dict(await fetch_fn())
                await self.set_with_jitter(prefix, cache_key, data, ttl)
                return self._to_ns(data)
            finally:
                await self._client.delete(lock_key)

        # Another request holds the lock: wait for it to fill the cache
        deadline = time.monotonic() + self.POLL_TIMEOUT
        while time.monotonic() < deadline:
            cached = await self.get(prefix, cache_key)
            if cached is not None:
                return cached
            await asyncio.sleep(self.POLL_INTERVAL)

        # Fallback: lock holder failed or was too slow
        return self._to_ns(alchemy_obj_to_dict(await fetch_fn()))

    async def set(self, prefix, key, url_obj: dict, ttl: int | None = None):
        await self._client.set(
            f"{prefix}:{key}", json.dumps(url_obj, default=str), ex=ttl
        )

    async def set_with_jitter(self, prefix, key, value, ttl: int):
        if ttl <= 0:
            raise ValueError(f"invalid ttl value of {ttl}")
        jitter = random.randint(0, int(ttl * 0.1))
        await self.set(prefix, key, value, ttl + jitter)

    


cache = Cache()