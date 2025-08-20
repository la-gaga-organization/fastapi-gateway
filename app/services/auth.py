from datetime import datetime, timedelta

from jose import jwt

from app.core.config import settings

# Carico le chiavi
PRIVATE_KEY = settings.PRIVATE_KEY
PUBLIC_KEY = settings.PUBLIC_KEY

with open(PRIVATE_KEY, "r") as f:
    private_key = f.read()

with open(PUBLIC_KEY, "r") as f:
    public_key = f.read()

ALGORITHM = "RS256"


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