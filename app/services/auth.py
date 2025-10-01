from datetime import datetime, timedelta

from fastapi import HTTPException
from passlib.context import CryptContext

from app.core.config import settings
from app.core.logging import get_logger
from app.db.session import get_db
from app.models.accessToken import AccessToken
from app.models.refreshToken import RefreshToken
from app.models.session import Session
from app.models.user import User
from app.schemas.auth import UserLogin, TokenResponse, TokenRequest, UserRegistration
from app.services.http_client import HttpClientException, HttpMethod, HttpUrl, HttpParams, send_request

logger = get_logger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Custom exception per invalid credentials
class InvalidCredentialsException(HttpClientException):
    def __init__(self, message: str):
        self.message = "Unauthorized"
        self.status_code = 401
        self.url = "/login"
        self.server_message = message
        # super().__init__("Unauthorized", message, 401, "/login")

    pass


# Custom exception per invalid session
class InvalidSessionException(HttpClientException):
    def __init__(self, message: str):
        self.message = "Forbidden"
        self.status_code = 403
        self.url = "/logout"
        self.server_message = message
        # super().__init__("Forbidden", message, 403, "/logout")

    pass


# Custom exception per invalid token
class InvalidTokenException(HttpClientException):
    def __init__(self, message: str):
        self.message = "Unauthorized"
        self.status_code = 401
        self.url = "/token/verify"
        self.server_message = message
        # super().__init__("Unauthorized", message, 401, "/token/verify")

    pass


async def create_access_token(data: dict, expire_minutes: int = settings.ACCESS_TOKEN_EXPIRE_MINUTES) -> dict:
    """Crea un token di accesso (access token) utilizzando il servizio di autenticazione esterno.

    Args:
        data (dict): Dati da includere nel payload del token.
        expire_minutes (int, optional): Tempo di scadenza in minuti. Defaults to settings.ACCESS_TOKEN_EXPIRE_MINUTES.

    Raises:
        HttpClientException: Eccezione sollevata in caso di errore nella richiesta HTTP.

    Returns:
        str: Il token di accesso creato.
    """
    try:
        params = HttpParams(data)
        if expire_minutes:
            params.add_param("expires_in", expire_minutes)

        response = await send_request(
            url=HttpUrl.TOKEN_SERVICE,
            method=HttpMethod.POST,
            endpoint="/token/create",
            _params=params
        )
        return response.data
    except HttpClientException as e:
        raise e


async def create_refresh_token(data: dict, expire_days: int = settings.REFRESH_TOKEN_EXPIRE_DAYS) -> dict:
    """Crea un token di refresh (refresh token) utilizzando il servizio di autenticazione esterno.
    Args:
        data (dict): Dati da includere nel payload del token.
        expire_days (int, optional): Tempo di scadenza in giorni. Defaults to settings.REFRESH_TOKEN_EXPIRE_DAYS.

    Raises:
        HttpClientException: Eccezione sollevata in caso di errore nella richiesta HTTP.

    Returns:
        str: Il token di refresh creato.
    """
    try:
        params = HttpParams(data)
        if expire_days:
            params.add_param("expires_in", expire_days * 24 * 60)  # Converti giorni in minuti

        response = await send_request(
            url=HttpUrl.TOKEN_SERVICE,
            method=HttpMethod.POST,
            endpoint="/token/create",
            _params=params
        )
        return response.data
    except HttpClientException as e:
        raise e


async def create_new_user(data: dict) -> dict:
    """Crea un nuovo utente utilizzando il servizio utenti esterno.

    Args:
        data (dict): Dati dell'utente da creare.

    Raises:
        HttpClientException: Eccezione sollevata in caso di errore nella richiesta HTTP.

    Returns:
        dict: Dati dell'utente creato.
    """
    try:
        params = HttpParams(data)
        response = await send_request(
            url=HttpUrl.USERS_SERVICE,
            method=HttpMethod.POST,
            endpoint="/users/",
            _params=params
        )
        return response.data
    except HttpClientException as e:
        raise e


async def verify_token(token: str) -> dict:
    try:
        params = HttpParams({"token": token})
        response = await send_request(
            url=HttpUrl.TOKEN_SERVICE,
            method=HttpMethod.POST,
            endpoint="/token/verify",
            _params=params
        )
        return response.data
    except HttpClientException as e:
        raise e


def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)


async def login(user_login: UserLogin):
    db = next(get_db())
    try:
        user = db.query(User).filter(User.username == user_login.username).first()
        if not user or not verify_password(user_login.password, str(user.hashed_password)):
            raise InvalidCredentialsException("Invalid credentials")

        db_session = Session(
            user_id=user.id,
            expires_at=datetime.now() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        )
        db.add(db_session)
        db.commit()
        db.refresh(db_session)

        access_token_response = await create_access_token(
            data={"username": user.username, "user_id": user.id, "session_id": db_session.id})
        access_token = access_token_response["token"]
        refresh_token_response = await create_refresh_token(
            data={"username": user.username, "user_id": user.id, "session_id": db_session.id})
        refresh_token = refresh_token_response["token"]

        db_access_token = AccessToken(
            session_id=db_session.id,
            token=access_token
        )
        db.add(db_access_token)
        db.commit()
        db.refresh(db_access_token)
        db_refresh_token = RefreshToken(
            session_id=db_session.id,
            token=refresh_token,
            accessToken_id=db_access_token.id
        )
        db.add(db_refresh_token)
        db.commit()
        db.refresh(db_refresh_token)
        return TokenResponse(access_token=access_token, refresh_token=refresh_token)
    except InvalidCredentialsException as e:
        raise e
    except HttpClientException as e:
        raise e
    except Exception as e:
        logger.error(f"Unexpected error during authentication: {str(e)}")
        raise HttpClientException("Internal Server Error", server_message="Swiggity Swoggity, U won't find my log",
                                  status_code=500, url="/auth/login")


async def refresh_token(refresh_token: TokenRequest) -> TokenResponse:
    payload = await verify_token(refresh_token.token)
    if not payload or not payload["verified"]:
        raise InvalidTokenException("Invalid refresh token")

    db = next(get_db())
    db_old_refresh_token = db.query(RefreshToken).filter(RefreshToken.token == refresh_token.token).join(
        AccessToken).first()
    if not db_old_refresh_token:
        raise InvalidTokenException("Refresh token not found")

    session = db.query(Session).filter(Session.id == db_old_refresh_token.session_id).first()
    if not session or not session.is_active:
        raise InvalidTokenException("Session is inactive or does not exist")
    if session.is_blocked:
        raise InvalidTokenException("Session is blocked")
    if session.expires_at < datetime.now():
        raise InvalidTokenException("Session expired")

    if db_old_refresh_token.is_expired:
        # segno la sessione come non attiva e bloccata, perché è stato riusato un token già usato
        session.is_active = False
        session.is_blocked = True
        db.commit()
        db.refresh(session)
        # segno tutti i token associati alla sessione come scaduti
        db.query(AccessToken).filter(AccessToken.session_id == session.id).update({"is_expired": True})
        db.query(RefreshToken).filter(RefreshToken.session_id == session.id).update({"is_expired": True})
        db.commit()

        raise InvalidTokenException("Refresh token expired, Session blocked")

    access_token_response = await create_access_token(
        {"username": payload["username"], "user_id": payload["user_id"], "session_id": session.id})
    refresh_token_response = await create_refresh_token(
        {"username": payload["username"], "user_id": payload["user_id"], "session_id": session.id},
        expire_days=(
                session.expires_at - datetime.now()).days)
    access_token = access_token_response["token"]
    refresh_token = refresh_token_response["token"]
    # Segno i vecchi token come scaduti
    db_old_refresh_token.is_expired = True
    db.commit()
    db.refresh(db_old_refresh_token)
    db_old_refresh_token.accessToken.is_expired = True

    # Creo nuovi token
    db_access_token = AccessToken(
        session_id=session.id,
        token=access_token,
    )
    db.add(db_access_token)
    db.commit()
    db.refresh(db_access_token)
    db_refresh_token = RefreshToken(
        session_id=session.id,
        token=refresh_token,
        accessToken_id=db_access_token.id
    )
    db.add(db_refresh_token)
    db.commit()
    db.refresh(db_refresh_token)

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


async def logout(access_token: TokenRequest):
    payload = await verify_token(access_token.token)
    if not payload or not payload["verified"]:
        raise InvalidTokenException("Invalid access token")

    if payload["expired"]:
        raise InvalidTokenException("Access token expired")

    db = next(get_db())
    session = db.query(Session).filter(Session.id == payload["session_id"]).first()
    if not session:
        raise InvalidSessionException("Session does not exist")

    # Segno la sessione come non attiva
    session.is_active = False
    db.commit()
    db.refresh(session)

    # Segno tutti i token associati alla sessione come scaduti
    db.query(AccessToken).filter(AccessToken.session_id == session.id).update({"is_expired": True})
    db.query(RefreshToken).filter(RefreshToken.session_id == session.id).update({"is_expired": True})
    db.commit()

    return {"detail": "Logout successful"}


async def register(user: UserRegistration) -> TokenResponse:
    # TODO: Valutare l'hashing della password prima di inviarla al servizio utenti
    # hashed_password = pwd_context.hash(user.password)

    create_user_response = await create_new_user(
        data={"username": user.username, "name": user.name, "surname": user.surname, "email": user.email, "hashed_password": user.password})
    if not create_user_response or "id" not in create_user_response:
        raise HttpClientException("Internal Server Error", server_message="User creation failed", status_code=500,
                                  url="/auth/register")

    # Login automatico dopo la registrazione
    return await login(UserLogin(username=user.username, password=user.password))

# TODO: Aggiungere job per pulizia sessioni e token scaduti
async def validate_session(access_token: str) -> None:
    """Controlla se il token di accesso è valido e la sessione associata è attiva.

    Args:
        access_token (str): Il token di accesso da convalidare.

    Raises:
        InvalidTokenException: Se il token di accesso non è valido.
        InvalidTokenException: Se il token di accesso è scaduto.
        HTTPException: Se si verifica un errore imprevisto durante la convalida.

    Returns:
        bool: True se la sessione è valida, altrimenti False.
    """
    try:
        payload = await verify_token(access_token)
        if not payload or not payload["verified"]:
            raise InvalidTokenException("Invalid access token")

        db = next(get_db())

        if payload["expired"]:
            # Segna il token come scaduto
            session = db.query(Session).filter(Session.id == payload["session_id"]).first()
            if session:
                # Segna il token access come scaduto
                db.query(AccessToken).filter(AccessToken.session_id == session.id).update({"is_expired": True})
                db.commit()
                raise InvalidTokenException("Access token expired")
            else:
                raise InvalidTokenException("Access token is of an expired session")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during session validation: {str(e)}")
        raise HTTPException(status_code=500, detail={"message": "Internal Server Error",
                                                     "stack": "Swiggity Swoggity, U won't find my log",
                                                     "url": "auth/validate_session"})
