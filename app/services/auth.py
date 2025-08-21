from datetime import datetime, timedelta

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.db.session import get_db
from app.models.accessToken import AccessToken
from app.models.refreshToken import RefreshToken
from app.models.session import Session
from app.models.user import User
from app.schemas.auth import UserLogin

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Carico le chiavi
PRIVATE_KEY = settings.PRIVATE_KEY
PUBLIC_KEY = settings.PUBLIC_KEY

with open(PRIVATE_KEY, "r") as f:
    private_key = f.read()

with open(PUBLIC_KEY, "r") as f:
    public_key = f.read()

ALGORITHM = "RS256"


# Custom exception per invalid credentials
class InvalidCredentialsException(Exception):
    pass


# Custom exception per invalid session
class InvalidSessionException(Exception):
    pass


# Custom exception per invalid token
class InvalidTokenException(Exception):
    pass


def create_access_token(data: dict, expire_minutes: int = settings.ACCESS_TOKEN_EXPIRE_MINUTES):
    to_encode = data.copy()
    expire = datetime.now() + timedelta(minutes=expire_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, private_key, algorithm=ALGORITHM)


def create_refresh_token(data: dict, expire_days: int = settings.REFRESH_TOKEN_EXPIRE_DAYS):
    to_encode = data.copy()
    expire = datetime.now() + timedelta(days=expire_days)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, private_key, algorithm=ALGORITHM)


def verify_token(token: str):
    try:
        payload = jwt.decode(token, public_key, algorithms=[ALGORITHM])
        return payload
    except Exception:
        return None


def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)


def login(user_login: UserLogin):
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

        access_token = create_access_token(data={"sub": user.username, "user_id": user.id, "session_id": db_session.id})
        refresh_token = create_refresh_token(
            data={"sub": user.username, "user_id": user.id, "session_id": db_session.id})

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
        return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}
    except InvalidCredentialsException as e:
        raise e
    except Exception as e:
        print(e)
        raise Exception("Internal server error") from e


def refresh_token(refresh_token: str):
    payload = verify_token(refresh_token)
    if not payload or "sub" not in payload:
        raise InvalidTokenException("Invalid refresh token")

    db = next(get_db())
    db_old_refresh_token = db.query(RefreshToken).filter(RefreshToken.token == refresh_token).join(AccessToken).first()
    if not db_old_refresh_token:
        raise InvalidTokenException("Refresh token invalid")

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

    access_token = create_access_token(
        {"sub": payload["sub"], "user_id": payload.get("user_id"), "session_id": session.id})
    refresh_token = create_refresh_token(
        {"sub": payload["sub"], "user_id": payload.get("user_id"), "session_id": session.id},
        expire_days=(
                session.expires_at - datetime.now()).days)  # Scadenza del refresh token uguale a quella della sessione
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

    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


def logout(session_id: int):
    db = next(get_db())
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise InvalidSessionException("Session does not exist")

    # Segno la sessione come non attiva
    session.is_active = False
    db.commit()
    db.refresh(session)

    # Segno tutti i token associati alla sessione come scaduti
    db.query(AccessToken).filter(AccessToken.session_id == session_id).update({"is_expired": True})
    db.query(RefreshToken).filter(RefreshToken.session_id == session_id).update({"is_expired": True})
    db.commit()

    return {"detail": "Logout successful"}
