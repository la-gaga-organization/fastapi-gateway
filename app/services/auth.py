from datetime import datetime, timedelta

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.db.session import get_db
from app.models.session import Session
from app.models.token import Token
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


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, private_key, algorithm=ALGORITHM)


def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
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
        access_token = create_access_token(data={"sub": user.username, "user_id": user.id})
        refresh_token = create_refresh_token(data={"sub": user.username, "user_id": user.id})

        db_session = Session(
            user_id=user.id,
            expires_at=datetime.now() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        )
        db.add(db_session)
        db.commit()
        db.refresh(db_session)
        db_access_token = Token(
            session_id=db_session.id,
            token=access_token,
            token_type="access"
        )
        db.add(db_access_token)
        db.commit()
        db.refresh(db_access_token)
        db_refresh_token = Token(
            session_id=db_session.id,
            token=refresh_token,
            token_type="refresh"
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
