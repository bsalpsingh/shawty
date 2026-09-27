import redis.asyncio as redis
import json
from datetime import datetime
from types import SimpleNamespace
import os

class RedisCache:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, host=None, port=None):
        if not hasattr(self, "_initialized"):
            self._client = redis.Redis(
                host=host or os.environ.get("REDIS_HOST", "127.0.0.1"),
                port=int(port or os.environ.get("REDIS_PORT", 6379)),
                decode_responses=True
        )
        self._initialized = True

    async def get(self, prefix,key) -> SimpleNamespace | None:
        data = await self._client.get(f"{prefix}:{key}")
       
        if data is None:
            return None
        obj = json.loads(data)
        # restore expires_at from ISO string back to datetime
        if obj.get("expires_at"):
            obj["expires_at"] = datetime.fromisoformat(obj["expires_at"])

        return SimpleNamespace(**obj)

    async def set(self,  prefix,key,url_obj, ttl: int | None = None):
    
        await self._client.set(f"{prefix}:{key}", json.dumps(url_obj), ex=ttl)


cache = RedisCache()
