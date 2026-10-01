from fastapi import APIRouter, Depends, responses, Request, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, DBAPIError, SQLAlchemyError
from sqlalchemy import select, delete
from datetime import datetime, timezone
from fastapi import BackgroundTasks

from app.db.database import get_db, get_db_util
from app.schema.url import UrlPayload
from app.models.models import URL
from app.utils.utils import alchemy_obj_to_dict, set_with_jitter, refresh_cache_entry, get_unique_short_code, to_dict
from app.core.publisher import publisher
from app.core.cache import cache
from typing import Literal

main_router = APIRouter(prefix="", tags=["URLS"])


async def clean_expired_urls(batch_size: int = 1000):
    now = datetime.now(timezone.utc)
    total = 0

    while True:
        async with get_db_util() as db:
            ids = (await db.execute(select(URL.id).where(URL.expires_at.is_not(None), URL.expires_at < now).limit(batch_size))).scalars().all()
            if len(ids) == 0:
                break
            await db.execute(delete(URL).where(URL.id.in_(ids)))
            await db.commit()
            total += len(ids)
    return total


@main_router.post("/short-url")
async def CreateShortURL(body: UrlPayload, request: Request, db: AsyncSession = Depends(get_db)):

    shortUrl = f"{get_unique_short_code()[-8:]}"

    url = URL(url=str(body.url).rstrip("/"), shortURL=shortUrl,
              user_id=1, expires_at=body.expires_at)
    db.add(url)

    try:
        await db.commit()
        await db.refresh(url)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=409, detail={
                "status": "error",
                "CODE": "CONFLICT",
                "message": "Short URL collision, please retry",

            })
    except DBAPIError:
        await db.rollback()
        raise HTTPException(status_code=400, detail={
            "status": "error",
            "CODE": "BAD_REQUEST",
            "message": "invalid value provided"

        })
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(
            status_code=500, detail={
                "status": "error",
                "CODE": "INTERNAL_SERVER_ERROR",
                "message": "database error try later"

            })

    base = str(request.base_url).rstrip("/")
    return responses.JSONResponse(status_code=201, content={
        "status": "success",
        "url": url.url,
        "shortURL": f"{base}/{url.shortURL}",
    })


@main_router.get("/urls")
async def getMyUrls(request: Request, db: AsyncSession = Depends(get_db), skip: int = Query(0, ge=0), limit: int = Query(10, ge=5, le=100),
                    order: Literal["asc", "desc"] = "desc"):
    try:

        column = URL.created_at.desc() if order == "desc" else URL.created_at.asc()

        result = await db.execute(select(URL).where(URL.user_id == 1).order_by(column, URL.id).offset(skip).limit(limit))
        urls = result.scalars().all()

        base = str(request.base_url).rstrip("/")
        urls_data = [
            {**alchemy_obj_to_dict(u), "shortURL": f"{base}/{u.shortURL}"}
            for u in urls
        ]
        return responses.JSONResponse(status_code=200, content={
            "status": "success",
            "urls": urls_data
        })
    except DBAPIError:
        await db.rollback()
        raise HTTPException(status_code=400, detail={
            "status": "error",
            "CODE": "BAD_REQUEST",
            "message": "invalid value provided"

        })
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(
            status_code=500, detail={
                "status": "error",
                "CODE": "INTERNAL_SERVER_ERROR",
                "message": "database error try later"

            })


async def sync_cache_from_db(short_code):
    async with get_db_util() as db:

        try:

            result = await db.execute(
                select(URL).where(URL.shortURL == short_code, URL.user_id == 1)
            )
            url_obj = result.scalar_one_or_none()

            if url_obj is None:
                raise HTTPException(
                    status_code=404, detail={
                        "status": "error",
                        "CODE": "NOT_FOUND",
                        "message": "URL not found"
                    })

            await set_with_jitter("short_url", short_code, alchemy_obj_to_dict(url_obj), ttl=3600)
            return url_obj
        except SQLAlchemyError:
            await db.rollback()
            raise HTTPException(
                status_code=500, detail={
                    "status": "error",
                    "CODE": "INTERNAL_SERVER_ERROR",
                    "message": "database error try later"

                })


@main_router.get("/{short_code}")
async def gotoUrl(short_code: str, background_task: BackgroundTasks, req: Request):

    cached_url_record = await cache.get("short_url", short_code)

    if cached_url_record is None:
        cached_url_record = await sync_cache_from_db(short_code)

    else:
        background_task.add_task(
            refresh_cache_entry, f"short_url:{short_code}", 3600, 0.2, lambda: sync_cache_from_db(short_code))
    if cached_url_record.expires_at is not None and cached_url_record.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=410, detail={
            "status": "error",
            "CODE": "GONE",
            "message": "URL has expired"

        })

    target = cached_url_record.url.rstrip("/")
    if not target.startswith(("http://", "https://")):
        target = f"https://{target}"

    background_task.add_task(publisher.send, "analytics", {
        **to_dict(cached_url_record), "ip_addr": req.client.host if req.client else "unknown", "ref": req.headers.get("referer"), "ts": datetime.now(timezone.utc).isoformat()})

    return responses.RedirectResponse(url=target)
