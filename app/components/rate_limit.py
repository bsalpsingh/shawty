# app/components/rate_limit.py
import math
from fastapi import HTTPException, Request, Response

from app.components.token_bucket import TokenBucket


def rate_limit(capacity: int = 10, refill_rate: int = 1, refill_interval: float = 1.0, scope: str = "default"):
    bucket = TokenBucket(capacity, refill_rate, refill_interval)

    async def dependency(request: Request, response: Response):
        client_id = request.client.host if request.client else "unknown"
        key = f"rl:{scope}:{client_id}"

        allowed, remaining = await bucket.allow(key)

        response.headers["X-RateLimit-Limit"] = str(capacity)
        response.headers["X-RateLimit-Remaining"] = str(int(remaining))

        if not allowed:
            retry_after = math.ceil(refill_interval / refill_rate)
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded",
                headers={"Retry-After": str(retry_after)},
            )

    return dependency