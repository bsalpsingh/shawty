import time
from app.components.cache import cache

TOKEN_BUCKET_SCRIPT = """
local key = KEYS[1]
local capacity = tonumber(ARGV[1])
local refill_rate = tonumber(ARGV[2])
local refill_interval = tonumber(ARGV[3])
local now = tonumber(ARGV[4])

local bucket = redis.call('HMGET', key, 'tokens', 'last_refill')
local tokens = tonumber(bucket[1])
local last_refill = tonumber(bucket[2])

if tokens == nil then
    tokens = capacity
    last_refill = now
end

local refills = math.floor((now - last_refill) / refill_interval)
if refills > 0 then
    tokens = math.min(capacity, tokens + refills * refill_rate)
    last_refill = last_refill + refills * refill_interval
end

local allowed = 0
if tokens >= 1 then
    tokens = tokens - 1
    allowed = 1
end

redis.call('HSET', key, 'tokens', tokens, 'last_refill', last_refill)
-- expire idle buckets so keys don't pile up
redis.call('EXPIRE', key, math.ceil(capacity / refill_rate * refill_interval) * 2)

return {allowed, tostring(tokens)}
"""


class TokenBucket:
    def __init__(self, capacity: int = 10, refill_rate: int = 1, refill_interval: float = 1.0):
        self.redis = cache.redis_client
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.refill_interval = refill_interval
        self._script = self.redis.register_script(TOKEN_BUCKET_SCRIPT)

    async def allow(self, key: str) -> tuple[bool, float]:
        result = await self._script(
            keys=[key],
            args=[self.capacity, self.refill_rate, self.refill_interval, time.time()],
        )
        return bool(result[0]), float(result[1])


limiter = TokenBucket(capacity=10, refill_rate=1, refill_interval=1.0)