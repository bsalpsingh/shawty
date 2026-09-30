import os
import asyncio
import clickhouse_connect
from typing import List


class ClickHouseReader:
    _client = None
    _lock = asyncio.Lock()

    @classmethod
    async def get_client(cls):
        # check if client is there or not

        # if client return client
        # else initalize client
        if cls._client is None:

            async with cls._lock:
                if cls._client is None:   # always check again as there can be race conditons
                    cls._client = await clickhouse_connect.get_async_client(
                        host=os.environ.get("CLICKHOUSE_HOST", "localhost"),
                        port=int(os.environ.get("CLICKHOUSE_PORT", "8123")),
                        username=os.environ.get("CLICKHOUSE_USER", "app"),
                        password=os.environ.get("CLICKHOUSE_PASSWORD", ""),
                        database=os.environ.get("CLICKHOUSE_DB", "analytics"),
                    )
        return cls._client

    @classmethod
    async def fetch(cls, sql: str, params: dict | None = None) -> List[dict]:
        c = await cls.get_client()
        result = await c.query(sql, parameters=params or {})
        return list(result.named_results())
