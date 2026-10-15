from sqlalchemy import String, ForeignKey,func
from sqlalchemy.orm import  Mapped, mapped_column, relationship,deferred
from sqlalchemy import DateTime
from typing import List
from app.db.database import Base
from datetime import datetime
import uuid
from sqlalchemy.dialects.postgresql import UUID 
import enum
from sqlalchemy import String

class Role(str, enum.Enum):
    user = "user"
    admin = "admin"


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50),nullable=False)
    email: Mapped[str] = mapped_column(String(255), index=True, unique=True,nullable=False)
    supabase_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), unique=True, index=True, nullable=True
    )
    role: Mapped[str] = mapped_column(
        String(20), nullable=False, default=Role.user.value,
        server_default=Role.user.value,
    )
    urls: Mapped[List["URL"]] = relationship(back_populates="user")

class URL(Base):
    __tablename__ = "urls"
    id: Mapped[int] = mapped_column(primary_key=True)
    url: Mapped[str] = mapped_column(String(500))
    shortURL: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    user: Mapped["User"] = relationship(back_populates="urls")
    expires_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True), nullable=True,index=True)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),nullable=False,server_default=func.now())