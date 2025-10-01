from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class UserLogin(BaseModel):
    email: str
    password: str


class UserRegistration(BaseModel):
    name: str
    surname: str
    email: str
    password: str


class UserOut(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime
    updated_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"


class TokenRequest(BaseModel):
    token: str
