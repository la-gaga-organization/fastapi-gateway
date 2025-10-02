from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from app.core.logging import get_logger
from app.schemas.users import ChangePasswordRequest, ChangePasswordResponse, UpdateUserRequest, UpdateUserResponse, DeleteUserResponse
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

@router.patch("/", response_model=UpdateUserResponse)
async def update_user_self(new_data: UpdateUserRequest, request: Request):
    try:
        payload = await auth.verify_token(request.headers.get("Authorization").replace("Bearer ", "").strip())
        return await users.update_user(payload["user_id"], new_data)
    except HttpClientException as e:
        raise HTTPException(status_code=e.status_code,
                            detail={"message": e.message, "stack": e.server_message, "url": e.url})
    except Exception as e:
        logger.error(f"Unexpected error during self user update: {str(e)}")
        raise HTTPException(status_code=500, detail={"message": "Internal Server Error",
                                                     "stack": "Swiggity Swoggity, U won't find my log",
                                                     "url": "users/update_user_self"})
        
@router.patch("/{user_id}", response_model=UpdateUserResponse)
async def update_user(user_id: int, new_data: UpdateUserRequest, request: Request):
    try:
        # TODO: verificare che l'utente abbia i permessi per modificare un altro utente
        await auth.verify_token(request.headers.get("Authorization").replace("Bearer ", "").strip())
        return await users.update_user(user_id, new_data)
    except HttpClientException as e:
        raise HTTPException(status_code=e.status_code,
                            detail={"message": e.message, "stack": e.server_message, "url": e.url})
    except Exception as e:
        logger.error(f"Unexpected error during user update: {str(e)}")
        raise HTTPException(status_code=500, detail={"message": "Internal Server Error",
                                                     "stack": "Swiggity Swoggity, U won't find my log",
                                                     "url": "users/update_user"})
        
@router.delete("/{user_id}", response_model=DeleteUserResponse)
async def delete_user(user_id: int, request: Request):
    try:
        # TODO: verificare che l'utente abbia i permessi per eliminare un altro utente
        await auth.verify_token(request.headers.get("Authorization").replace("Bearer ", "").strip())
        return await users.delete_user(user_id)
    except HttpClientException as e:
        raise HTTPException(status_code=e.status_code,
                            detail={"message": e.message, "stack": e.server_message, "url": e.url})
    except Exception as e:
        logger.error(f"Unexpected error during user deletion: {str(e)}")
        raise HTTPException(status_code=500, detail={"message": "Internal Server Error",
                                                     "stack": "Swiggity Swoggity, U won't find my log",
                                                     "url": "users/delete_user"})