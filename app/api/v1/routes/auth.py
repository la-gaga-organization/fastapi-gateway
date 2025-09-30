from __future__ import annotations

from fastapi import APIRouter, HTTPException, Depends

from app.schemas.auth import UserLogin, TokenResponse, TokenRequest
from app.services import auth
from app.services.auth import create_access_token
from app.services.http_client import HttpClientException

router = APIRouter()

# TODO: aggiungo la gestione degli errori
# TODO: implemento creazione utente e modifica password (passando dal servizio dedicato)
# TODO: implemento il routing tra servizi con la gestione delle sessioni
@router.post("/login", response_model=TokenResponse)
async def login(user: UserLogin):
    try:
        return await auth.login(user)
    except HttpClientException as e:
        raise HTTPException(status_code=e.status_code, detail={"message": e.message, "stack": e.server_message, "url": e.url})
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Internal Server Error", "stack": str(e), "url": None})

@router.post("/refresh", response_model=TokenResponse)
async def post_refresh_token(refresh_token: TokenRequest):
    try:
        return await auth.refresh_token(refresh_token)
    except HttpClientException as e:
        raise HTTPException(status_code=e.status_code, detail={"message": e.message, "stack": e.server_message, "url": e.url})
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Internal Server Error", "stack": str(e), "url": None})


@router.post("/logout")
async def logout(access_token: TokenRequest):
    try:
        return await auth.logout(access_token)
    except auth.InvalidTokenException as e:
        raise HTTPException(status_code=401, detail=str(e))
    except auth.InvalidSessionException as e:
        raise HTTPException(status_code=403, detail=str(e))
