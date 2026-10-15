from fastapi import APIRouter, Depends, responses
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.components.rate_limit import rate_limit
from app.schema.user import UserSignUpPayload
from app.utils.auth import hash_password
from app.db.queries import add_user

user_router = APIRouter(prefix="/users", tags=["URLS"],    dependencies=[
                        Depends(rate_limit(capacity=20, scope="users"))])


@user_router.post("/signup")
async def signup(payload: UserSignUpPayload, db: AsyncSession = Depends(get_db)):

    hash = hash_password(payload.password)
    payload.password = hash
    await add_user(db=db, user=payload)
    return responses.JSONResponse(status_code=201, content={
        "status": "success",
        "message": "user created successfully"
    })
