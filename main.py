from fastapi import FastAPI

from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api.router import router


# from sqlalchemy import select
from app.db.database import engine, Base, get_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(lifespan=lifespan)
app.include_router(router=router)
