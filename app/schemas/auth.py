from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr

from app.services.http_client import OrientatiResponse


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserRegistration(BaseModel):
    username: str
    name: str
    surname: str
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    username: str
    email: EmailStr
    created_at: datetime
    updated_at: datetime


class TokenResponse(OrientatiResponse):
    def __init__(self, status_code: int, access_token: str, refresh_token: str, token_type: str = "Bearer"):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.token_type = token_type
        token_data = {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "token_type": self.token_type
        }
        super().__init__(status_code, token_data)


class TokenRequest(BaseModel):
    token: str


