from __future__ import annotations

from fastapi import APIRouter, HTTPException, Depends

from app.api.deps import get_current_user
from app.schemas.auth import UserLogin, TokenResponse
from app.services import auth
from app.services.auth import create_access_token
from app.services.http_client import HttpClientException

router = APIRouter()

# TODO: aggiungo la gestione degli errori
# TODO: modifico la gestione delle chiavi per rotazione dei secrets esterna
# TODO: implemento creazione utente e modifica password (passando dal servizio dedicato)
# TODO: implemento il routing tra servizi con la gestione delle sessioni
@router.post("/login", response_model=TokenResponse)
async def login(user: UserLogin):
    try:
        access_token = await create_access_token(data={"username": "gaga", "user_id": "1", "session_id": "1"}, expire_minutes=60)
        return TokenResponse(
            token=access_token,
            token_type="bearer",
        )
    except HttpClientException as e:
        raise HTTPException(status_code=e.status_code, detail={"message": e.message, "stack": e.server_message, "url": e.url})

@router.post("/refresh", response_model=TokenResponse)
def post_refresh_token(refresh_token: str):
    try:
        return auth.refresh_token(refresh_token)
    except auth.InvalidTokenException as e:
        raise HTTPException(status_code=401, detail=str(e))
    except auth.InvalidSessionException as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post("/logout")
def logout(current_user=Depends(get_current_user)):
    try:
        auth.logout(current_user["session_id"])
        return {"detail": "Logout successful"}
    except auth.InvalidTokenException as e:
        raise HTTPException(status_code=401, detail=str(e))
    except auth.InvalidSessionException as e:
        raise HTTPException(status_code=403, detail=str(e))
