from fastapi import APIRouter, Depends, responses, Request, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.db.queries import add_short_url, flush_urls, get_all_urls, get_short_url
from app.schema.url import UrlPayload
from app.core.publisher import publisher
from app.core.cache import cache
from app.utils.utils import alchemy_obj_to_dict, get_unique_short_code, to_dict
from datetime import datetime, timezone
from typing import Literal


main_router = APIRouter(prefix="", tags=["URLS"])


async def clean_expired_urls(batch_size: int = 1000):
    return await flush_urls(batch_size)


@main_router.post("/short-url")
async def CreateShortURL(body: UrlPayload, request: Request, db: AsyncSession = Depends(get_db)):

    short_url = f"{get_unique_short_code()[-8:]}"

    await add_short_url(db, url=str(body.url).rstrip("/"), short_url=short_url,
                        user_id=1, expires_at=body.expires_at)

    base = str(request.base_url).rstrip("/")
    return responses.JSONResponse(status_code=201, content={
        "status": "success",
        "url": str(body.url),
        "shortURL": f"{base}/{short_url}",
    })


@main_router.get("/urls")
async def getMyUrls(request: Request, db: AsyncSession = Depends(get_db), skip: int = Query(0, ge=0), limit: int = Query(10, ge=5, le=100),
                    order: Literal["asc", "desc"] = "desc"):

    urls = await get_all_urls(db, order, skip, limit)
    base = str(request.base_url).rstrip("/")
    urls_data = [
        {**alchemy_obj_to_dict(u),
         "shortURL": f"{base}/{u.shortURL}"}
        for u in urls
    ]

    return responses.JSONResponse(status_code=200, content={
        "status": "success",
        "urls": urls_data
    })


@main_router.get("/{short_code}")
async def gotoUrl(short_code: str, background_task: BackgroundTasks, req: Request, db: AsyncSession = Depends(get_db)):

    async def my_callback():
        data = await get_short_url(db, short_code)
        if data is None:
            raise HTTPException(status_code=404, detail={
                "status": "error",
                "CODE": "NOT FOUND",
                        "message": "URL not found"

            })
        return data

    cached_url_record = await cache.coalesce_cache("short_url", short_code, my_callback, 3600)

    if cached_url_record.expires_at is not None and (cached_url_record.expires_at) < datetime.now(timezone.utc):

        raise HTTPException(status_code=410, detail={
            "status": "error",
            "CODE": "GONE",
            "message": "URL has expired"

        })

    target = cached_url_record.url.rstrip("/")
    if not target.startswith(("http://", "https://")):
        target = f"https://{target}"

    publisher.send("analytics", {
        **to_dict(cached_url_record), "ip_addr": req.client.host if req.client else "unknown", "ref": req.headers.get("referer"), "ts": datetime.now(timezone.utc).isoformat()})
    return responses.RedirectResponse(url=target)

    return responses.RedirectResponse(url=target)
