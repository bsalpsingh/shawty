from fastapi import APIRouter, Depends, HTTPException
from app.core.clickhouse import ClickHouseReader  # must point to the file containing ClickHouseReader

analytics_router = APIRouter(prefix="/analytics",tags=["Analytics"])


def get_current_user():
    return {"id": 1, "name": "foobar"}


def to_code(short_url: str) -> str:
    # accepts "5D2XY9" or "http://localhost:8000/5D2XY9"
    return short_url.rstrip("/").split("/")[-1]


@analytics_router.get("/{short_url:path}/summary")
async def summary(short_url: str, user: dict = Depends(get_current_user)):
    rows = await ClickHouseReader.fetch(
        """
        SELECT count() AS clicks,
               uniq(ip_addr) AS unique_visitors,
               min(clicked_at) AS first_click,
               max(clicked_at) AS last_click
        FROM url_clicks
        WHERE short_url = {s:String} AND user_id = {u:UInt64}
        """,
        {"s": to_code(short_url), "u": user["id"]},
    )
    if not rows or rows[0]["clicks"] == 0:
        raise HTTPException(status_code=404, detail="No analytics found for this URL")
    return rows[0]


@analytics_router.get("/{short_url:path}/hourly")
async def hourly(short_url: str, days: int = 7, user: dict = Depends(get_current_user)):
    return await ClickHouseReader.fetch(
        """
        SELECT toStartOfHour(clicked_at) AS hour, count() AS clicks
        FROM url_clicks
        WHERE short_url = {s:String} AND user_id = {u:UInt64}
          AND clicked_at >= now() - INTERVAL {d:UInt16} DAY
        GROUP BY hour ORDER BY hour
        """,
        {"s": to_code(short_url), "u": user["id"], "d": days},
    )


@analytics_router.get("/{short_url:path}/referrers")
async def referrers(short_url: str, user: dict = Depends(get_current_user)):
    return await ClickHouseReader.fetch(
        """
        SELECT if(referrer = '', 'direct', referrer) AS referrer, count() AS clicks
        FROM url_clicks
        WHERE short_url = {s:String} AND user_id = {u:UInt64}
        GROUP BY referrer ORDER BY clicks DESC LIMIT 10
        """,
        {"s": to_code(short_url), "u": user["id"]},
    )