from fastapi import FastAPI

from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api.main_router import main_router
from app.api.analytics_router import analytics_router


# from sqlalchemy import select
from app.db.database import engine, Base, get_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(lifespan=lifespan)
app.include_router(router=main_router)
app.include_router(router=analytics_router)
