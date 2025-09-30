from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserLogin(BaseModel):
    username: str
    password: str


class UserRegistration(BaseModel):
    username: str
    email: EmailStr
    full_name: str | None = None
    password: str


class UserOut(BaseModel):
    id: int
    username: str
    email: EmailStr
    full_name: str | None = None
    created_at: datetime
    updated_at: datetime


class TokenResponse(BaseModel):
    token: str
    token_type: str
