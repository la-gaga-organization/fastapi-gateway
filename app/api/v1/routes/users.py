from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from app.core.logging import get_logger
from app.schemas.users import ChangePasswordRequest, ChangePasswordResponse
from app.services.http_client import HttpClientException
from app.services import users, auth

logger = get_logger(__name__)
router = APIRouter()

@router.post("/change_password", response_model=ChangePasswordResponse)
async def change_password(passwords: ChangePasswordRequest, request: Request):
    try:
        payload = await auth.verify_token(request.headers.get("Authorization").replace("Bearer ", "").strip())
        return await users.change_password(passwords, payload["user_id"])
    except HttpClientException as e:
        raise HTTPException(status_code=e.status_code,
                            detail={"message": e.message, "stack": e.server_message, "url": e.url})
    except Exception as e:
        logger.error(f"Unexpected error during change_password: {str(e)}")
        raise HTTPException(status_code=500, detail={"message": "Internal Server Error",
                                                     "stack": "Swiggity Swoggity, U won't find my log",
                                                     "url": "users/change_password"})
