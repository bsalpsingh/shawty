from fastapi import FastAPI

from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api.main_router import main_router
from app.api.analytics_router import analytics_router
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.api.main_router import clean_expired_urls

# from sqlalchemy import select
from app.db.database import engine, Base, get_db

scheduler=AsyncIOScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    scheduler.add_job(
        clean_expired_urls,
        "interval",
        hours=1,
        max_instances=1,
        coalesce=True,
    )
    scheduler.start()
    yield
    scheduler.shutdown()

app = FastAPI(lifespan=lifespan)
app.include_router(router=main_router)
app.include_router(router=analytics_router)
