from datetime import datetime, timedelta

from fastapi import HTTPException
from passlib.context import CryptContext
from requests import session

from app.core.config import settings
from app.core.logging import get_logger
from app.db.session import get_db
from app.models.session import Session
from app.models.user import User
from app.schemas.users import ChangePasswordRequest, ChangePasswordResponse
from app.services.http_client import HttpClientException, HttpMethod, HttpUrl, HttpParams, send_request

logger = get_logger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def change_password(passwords: ChangePasswordRequest, user_id: int) -> ChangePasswordResponse:
    try:
        params = HttpParams()
        params.add_param("user_id", user_id)
        params.add_param("old_password", passwords.old_password)
        params.add_param("new_password", passwords.new_password)
        await send_request(
            method=HttpMethod.POST,
            url=HttpUrl.USERS_SERVICE,
            endpoint="/users/change_password",
            _params=params
        )
    
        return ChangePasswordResponse()
    except HttpClientException:
        raise
    except Exception:
        raise HttpClientException("Internal Server Error", "Swiggity Swooty, U won't find my log", 500, "users/change_password")