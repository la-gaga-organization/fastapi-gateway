from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.core.logging import get_logger
from app.schemas.auth import UserLogin, TokenResponse, TokenRequest, UserRegistration
from app.services import auth
from app.services.http_client import OrientatiException, OrientatiResponse

logger = get_logger(__name__)
router = APIRouter()

@router.post("/login", response_model=OrientatiResponse)
async def login(user: UserLogin):
    try:
        return await auth.login(user)
    except OrientatiException as e:
        raise HTTPException(status_code=e.status_code,
                            detail={"message": e.message, "details": e.details, "url": e.url})


@router.post("/refresh", response_model=OrientatiResponse)
async def post_refresh_token(refresh_token: TokenRequest):
    try:
        return await auth.refresh_token(refresh_token)
    except OrientatiException as e:
        raise HTTPException(status_code=e.status_code,
                            detail={"message": e.message, "details": e.details, "url": e.url})


@router.post("/logout", response_model=OrientatiResponse)
async def logout(access_token: TokenRequest):
    try:
        return await auth.logout(access_token)
    except OrientatiException as e:
        raise HTTPException(status_code=e.status_code,
                            detail={"message": e.message, "details": e.details, "url": e.url})


@router.post("/register", response_model=OrientatiResponse)
async def register(user: UserRegistration):
    try:
        return await auth.register(user)
    except OrientatiException as e:
        raise HTTPException(status_code=e.status_code,
                            detail={"message": e.message, "details": e.details, "url": e.url})
