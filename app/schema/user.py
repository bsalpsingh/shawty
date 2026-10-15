import re
from pydantic import BaseModel, EmailStr, Field, field_validator


class UserSignUpPayload(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=64)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if re.search(r"\s", v):
            raise ValueError("Password must not contain whitespace")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain a lowercase letter")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain an uppercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain a digit")
        if not re.search(r"[^\w\s]", v):
            raise ValueError("Password must contain a special character")
        return v