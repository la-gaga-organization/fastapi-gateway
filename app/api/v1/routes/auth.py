from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.core.logging import get_logger
from app.schemas.auth import UserLogin, TokenResponse, TokenRequest, UserRegistration
from app.services import auth
from app.services.http_client import HttpClientException

logger = get_logger(__name__)
router = APIRouter()


# TODO: aggiungo la gestione degli errori
# TODO: implemento creazione utente e modifica password (passando dal servizio dedicato)
# TODO: implemento il routing tra servizi con la gestione delle sessioni
@router.post("/login", response_model=TokenResponse)
async def login(user: UserLogin):
    try:
        return await auth.login(user)
    except HttpClientException as e:
        raise HTTPException(status_code=e.status_code,
                            detail={"message": e.message, "stack": e.server_message, "url": e.url})
    except Exception as e:
        logger.error(f"Unexpected error during login: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail={"message": "Internal Server Error",
                                                     "stack": "Swiggity Swoggity, U won't find my log",
                                                     "url": "auth/login"})


@router.post("/refresh", response_model=TokenResponse)
async def post_refresh_token(refresh_token: TokenRequest):
    try:
        return await auth.refresh_token(refresh_token)
    except HttpClientException as e:
        raise HTTPException(status_code=e.status_code,
                            detail={"message": e.message, "stack": e.server_message, "url": e.url})
    except Exception as e:
        logger.error(f"Unexpected error during token refresh: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail={"message": "Internal Server Error",
                                                     "stack": "Swiggity Swoggity, U won't find my log",
                                                     "url": "auth/refresh"})


@router.post("/logout")
async def logout(access_token: TokenRequest):
    try:
        return await auth.logout(access_token)
    except auth.InvalidTokenException as e:
        raise HTTPException(status_code=401, detail=str(e))
    except auth.InvalidSessionException as e:
        raise HTTPException(status_code=403, detail=str(e))
    except HttpClientException as e:
        raise HTTPException(status_code=e.status_code,
                            detail={"message": e.message, "stack": e.server_message, "url": e.url})
    except Exception as e:
        logger.error(f"Unexpected error during logout: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail={"message": "Internal Server Error",
                                                     "stack": "Swiggity Swoggity, U won't find my log",
                                                     "url": "auth/logout"})


@router.post("/register", response_model=TokenResponse)
async def register(user: UserRegistration):
    try:
        return await auth.register(user)
    except HttpClientException as e:
        raise HTTPException(status_code=e.status_code,
                            detail={"message": e.message, "stack": e.server_message, "url": e.url})
    except Exception as e:
        logger.error(f"Unexpected error during registration: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail={"message": "Internal Server Error",
                                                     "stack": "Swiggity Swoggity, U won't find my log",
                                                     "url": "auth/register"})
