from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter

from app.schemas.auth import UserLogin, TokenResponse
from app.services.auth import create_access_token, create_refresh_token, verify_token

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
def login(user: UserLogin):
    if user.username == "admin" and user.password == "secret":
        access_token = create_access_token({"sub": user.username})
        refresh_token = create_refresh_token({"sub": user.username})
        return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}
    raise Exception("Invalid credentials")

#TODO: sposto la logica di business in un service separato, implemento il db per il refresh token e gestisco la scadenza dei token, aggiungo la gestione degli errori
#TODO: implemento la logica di logout per invalidare i token
#TODO: implermento la logica della rotazione dei refresh token, aggiungo inoltre il controllo e revoca totale per refresh token  scaduti
#TODO: considero l'idea della rotazione dei secrets
#TODO: controllo che funzionino i due token separati e tutto il resto.

@router.post("/refresh", response_model=TokenResponse)
def post_refresh_token(refresh_token: str):
    payload = verify_token(refresh_token)
    if payload:

        if "sub" not in payload:
            raise Exception("Invalid refresh token")
        if payload["exp"] < datetime.now().timestamp():
            raise Exception("Refresh token expired")

        access_token = create_access_token({"sub": payload["sub"]})
        return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}
    return None

def logout():
    # In a real application, you would invalidate the token here
    return {"message": "Logged out successfully"}