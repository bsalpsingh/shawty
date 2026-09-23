from fastapi import APIRouter, Depends, responses, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.schema.url import UrlPayload
from app.models.models import URL
from app.utils.utils import md5_to_base62
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError, DBAPIError, SQLAlchemyError
from sqlalchemy import select
from datetime import datetime, timezone
router = APIRouter(prefix="")


@router.post("/getShortUrl")
async def getShortUrl(body: UrlPayload, request: Request, db: AsyncSession = Depends(get_db)):
    shortUrl = f"{md5_to_base62(str(body.url))[0:6]}"

    url = URL(url=str(body.url), shortURL=shortUrl,
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

    return responses.JSONResponse(status_code=201, content={
        "status": "success",
        "url": url.url,              # the original long URL, unprefixed
        # domain + short code
        "shortURL": f"{str(request.base_url).rstrip("/")}/{url.shortURL}",
    })


@router.get("/urls")
async def getMyUrls(request:Request,db: AsyncSession = Depends(get_db)):
    print("url")
    try:
        result = await db.execute(select(URL).where(URL.user_id == 1))
        urls = result.scalars().all()
        print("urls",urls)

        urls_data = [
            {"id": u.id, "short_code": f"{str(request.base_url).rstrip("/")}/{u.shortURL}", "original_url": u.url}
            for u in urls
        ]
        return responses.JSONResponse(status_code=200, content={
            "status": "success",
            "urls": urls_data
        })
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



@router.get("/{short_code}")
async def gotoUrl(short_code: str, db: AsyncSession = Depends(get_db)):

    try:

        result = await db.execute(select(URL).where(URL.shortURL == short_code, URL.user_id == 1))
        url_obj = result.scalar_one()

        if url_obj.expires_at is not None and url_obj.expires_at < datetime.now(timezone.utc):
            raise HTTPException(status_code=403, detail="url has expired")
        target = url_obj.url
        if not target.startswith(("http://", "https://")):
            target = f"https://{target}"

        return responses.RedirectResponse(url=target)
    except:
        raise HTTPException(status_code=500, detail="something went wrong")


