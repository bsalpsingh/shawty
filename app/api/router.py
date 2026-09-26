from fastapi import APIRouter, Depends, responses, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, DBAPIError, SQLAlchemyError, NoResultFound
from sqlalchemy import select
from datetime import datetime, timezone
from fastapi import BackgroundTasks

from app.db.database import get_db
from app.schema.url import UrlPayload
from app.models.models import URL
from app.utils.utils import alchemy_obj_to_dict, set_with_jitter, refresh_cache_entry,get_unique_short_code
from app.core.redis import cache


router = APIRouter(prefix="")


@router.post("/getShortUrl")
async def getShortUrl(body: UrlPayload, request: Request, db: AsyncSession = Depends(get_db)):
    shortUrl = f"{get_unique_short_code()[0:6]}"

    url = URL(url=str(body.url).rstrip("/"), shortURL=shortUrl,
              user_id=1, expires_at=body.expires_at)
    db.add(url)

    try:
        await db.commit()
        await db.refresh(url)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=409, detail="Short URL collision, please retry")
    except DBAPIError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Invalid data provided")
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(
            status_code=500, detail="Database error, please try again later")

    base = str(request.base_url).rstrip("/")
    return responses.JSONResponse(status_code=201, content={
        "status": "success",
        "url": url.url,
        "shortURL": f"{base}/{url.shortURL}",
    })


@router.get("/urls")
async def getMyUrls(request: Request, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(URL).where(URL.user_id == 1))
        urls = result.scalars().all()

        base = str(request.base_url).rstrip("/")
        urls_data = [
            { **alchemy_obj_to_dict(u), "shortURL": f"{base}/{u.shortURL}" }
            for u in urls
        ]
        return responses.JSONResponse(status_code=200, content={
            "status": "success",
            "urls": urls_data
        })
    except DBAPIError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Invalid data provided")
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(
            status_code=500, detail="Database error, please try again later")


async def sync_cache_from_db(db, short_code):
    result = await db.execute(
        select(URL).where(URL.shortURL == short_code, URL.user_id == 1)
    )
    url_obj = result.scalar_one()
    
    if url_obj:
        # ttl optional
        await set_with_jitter(short_code, alchemy_obj_to_dict(url_obj), ttl=3600)
    return url_obj


@router.get("/{short_code}")
async def gotoUrl(short_code: str, background_task: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    try:
        cached_url_record = await cache.get(short_code)

        if cached_url_record is None:
            cached_url_record = await sync_cache_from_db(db, short_code)

        else:
            background_task.add_task(
                refresh_cache_entry, short_code, 3600, 0.2, lambda: sync_cache_from_db(db, short_code))
        if cached_url_record.expires_at is not None and cached_url_record.expires_at < datetime.now(timezone.utc):
            raise HTTPException(status_code=403, detail="url has expired")

        target = cached_url_record.url.rstrip("/")
        if not target.startswith(("http://", "https://")):
            target = f"https://{target}"

        return responses.RedirectResponse(url=target)

    except NoResultFound:
        raise HTTPException(status_code=404, detail="short url not found")
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(
            status_code=500, detail="Database error, please try again later")
