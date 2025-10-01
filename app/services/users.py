from passlib.context import CryptContext

from app.core.logging import get_logger
from app.schemas.users import ChangePasswordRequest, ChangePasswordResponse, UpdateUserRequest, UpdateUserResponse
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
    
async def update_user(user_id: int, new_data: UpdateUserRequest) -> UpdateUserResponse:
    try:
        params = HttpParams()
        params.add_param("username", new_data.username) if new_data.username else None
        params.add_param("email", new_data.email) if new_data.email else None
        params.add_param("name", new_data.name) if new_data.name else None
        params.add_param("surname", new_data.surname) if new_data.surname else None
        response = await send_request(
            method=HttpMethod.PATCH,
            url=HttpUrl.USERS_SERVICE,
            endpoint=f"/users/{user_id}",
            _params=params
        )
        return UpdateUserResponse()
    except HttpClientException:
        raise
    except Exception:
        raise HttpClientException("Internal Server Error", "Swiggity Swooty, U won't find my log", 500, "users/update_user")