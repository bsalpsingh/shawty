from fastapi import HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, DBAPIError, SQLAlchemyError
from sqlalchemy import select, delete
from datetime import datetime, timezone

from app.db.database import get_db_util
from app.models.models import URL
from typing import Literal
from app.components.cache import cache
from app.utils.utils import alchemy_obj_to_dict


async def get_short_url(db: AsyncSession, short_code: str):
    result = None

    result = await db.execute(
        select(URL).where(URL.shortURL == short_code)
    )
    return result.scalar_one_or_none()


async def add_short_url(db: AsyncSession, url: str, user_id: int, expires_at: datetime | None, short_url: str):

    url = URL(url=url.rstrip("/"), shortURL=short_url,
              user_id=user_id, expires_at=expires_at)
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

async def flush_urls(batch_size: int):
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


async def get_all_urls(
        db: AsyncSession,
        order: Literal["desc", "asc"],
        skip: int = Query(0, ge=0),
        limit: int = Query(10, ge=5, le=100)):

    try:

        column = URL.created_at.desc() if order == "desc" else URL.created_at.asc()

        result = await db.execute(select(URL).where(URL.user_id == 1).order_by(column, URL.id).offset(skip).limit(limit))
        urls = result.scalars().all()

        return urls
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
