import os
import jwt
from jwt import PyJWKClient
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

   # e.g. https://<ref>.supabase.co
from app.db.database import get_db
from app.db.queries import get_or_create_user
from app.models.models import User

from app.models.models import Role


supabase_url=os.getenv("SUPABASE_URL") or ""

jwks_client = PyJWKClient(f"{supabase_url}/auth/v1/.well-known/jwks.json")
bearer = HTTPBearer(auto_error=False)


def _unauthorized(msg: str = "Invalid or expired token") -> HTTPException:
    return HTTPException(
        status_code=401,
        detail={"status": "error", "CODE": "UNAUTHORIZED", "message": msg},
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    if creds is None:
        raise _unauthorized("Missing bearer token")

    token = creds.credentials
    try:
        signing_key = jwks_client.get_signing_key_from_jwt(token).key
        claims = jwt.decode(
            token,
            signing_key,
            algorithms=["RS256", "ES256"],
            audience="authenticated",
            issuer=f"{supabase_url}/auth/v1",
        )
    except jwt.PyJWTError:
        raise _unauthorized()

    meta = claims.get("user_metadata") or {}
    return await get_or_create_user(
        db,
        supabase_id=claims["sub"],
        email=claims.get("email"),
        name=meta.get("full_name") or meta.get("name"),
    )


def require_roles(*allowed: Role):
    async def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in {r.value for r in allowed}:
            raise HTTPException(
                status_code=403,
                detail={"status": "error", "CODE": "FORBIDDEN",
                        "message": "You don't have permission to do this"},
            )
        return user
    return checker