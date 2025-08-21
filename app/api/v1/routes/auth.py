from __future__ import annotations

from fastapi import APIRouter, HTTPException, Depends

from app.api.deps import get_current_user
from app.schemas.auth import UserLogin, TokenResponse
from app.services import auth
from app.services.auth import InvalidCredentialsException

router = APIRouter()


# TODO: aggiungo la gestione degli errori
# TODO: modifico la gestione delle chiavi per rotazione dei secrets esterna
# TODO: implemento creazione utente e modifica password (passando dal servizio dedicato)
@router.post("/login", response_model=TokenResponse)
def login(user: UserLogin):
    try:
        return auth.login(user)
    except InvalidCredentialsException as e:
        raise HTTPException(status_code=401, detail=str(e))


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
