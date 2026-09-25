import redis.asyncio as redis
import json
from datetime import datetime
from types import SimpleNamespace


class RedisCache:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, host="127.0.0.1", port=6379):
        if not hasattr(self, "_initialized"):
            self._client = redis.Redis(
                host=host, port=port, decode_responses=True)
            self._initialized = True

    async def get(self, key) -> SimpleNamespace | None:
        data = await self._client.get(key)
        if data is None:
            return None
        obj = json.loads(data)
        # restore expires_at from ISO string back to datetime
        if obj.get("expires_at"):
            obj["expires_at"] = datetime.fromisoformat(obj["expires_at"])

        return SimpleNamespace(**obj)

    async def set(self, key, url_obj, ttl: int | None = None):\
    
        await self._client.set(key, json.dumps(url_obj), ex=ttl)


cache = RedisCache()
