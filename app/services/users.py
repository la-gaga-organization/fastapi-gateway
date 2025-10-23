import json

from passlib.context import CryptContext

from app.core.logging import get_logger
from app.schemas.users import ChangePasswordRequest, ChangePasswordResponse, UpdateUserRequest, UpdateUserResponse, DeleteUserResponse
from app.services.http_client import OrientatiException, HttpMethod, HttpUrl, HttpParams, send_request
from app.db.session import get_db
from app.models.user import User
from datetime import datetime

logger = get_logger(__name__)

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

RABBIT_DELETE_TYPE = "DELETE"
RABBIT_UPDATE_TYPE = "UPDATE"
RABBIT_CREATE_TYPE = "CREATE"

async def change_password(passwords: ChangePasswordRequest, user_id: int) -> bool:
    try:
        old_password_hashed = pwd_context.hash(passwords.old_password)
        new_password_hashed = pwd_context.hash(passwords.new_password)
        params = HttpParams()
        params.add_param("user_id", user_id)
        params.add_param("old_password", old_password_hashed)
        params.add_param("new_password", new_password_hashed)
        await send_request(
            method=HttpMethod.POST,
            url=HttpUrl.USERS_SERVICE,
            endpoint="/users/change_password",
            _params=params
        )
        return True
    except OrientatiException as e:
        raise e
    except Exception as e:
        raise OrientatiException(exc=e, url="users/change_password")


async def update_user(user_id: int, new_data: UpdateUserRequest) -> UpdateUserResponse:
    try:
        params = HttpParams()
        params.add_param("username", new_data.username) if new_data.username else None
        params.add_param("email", new_data.email) if new_data.email else None
        params.add_param("name", new_data.name) if new_data.name else None
        params.add_param("surname", new_data.surname) if new_data.surname else None
        await send_request(
            method=HttpMethod.PATCH,
            url=HttpUrl.USERS_SERVICE,
            endpoint=f"/users/{user_id}",
            _params=params
        )
        return UpdateUserResponse()
    except OrientatiException as e:
        raise e
    except Exception as e:
        raise OrientatiException(exc=e, url="users/update_user")

async def delete_user(user_id: int) -> DeleteUserResponse:
    try:
        await send_request(
            method=HttpMethod.DELETE,
            url=HttpUrl.USERS_SERVICE,
            endpoint=f"/users/{user_id}"
        )
        return DeleteUserResponse()
    except OrientatiException as e:
        raise e
    except Exception as e:
        raise OrientatiException(exc=e, url="users/delete_user")


async def update_from_rabbitMQ(message):
    async with message.process():
        try:
            db = next(get_db())
            response = message.body.decode()
            json_response = json.loads(response)
            msg_type = json_response["type"]
            data = json_response["data"]

            logger.info(f"Received message from RabbitMQ: {msg_type} - {data}")

            user = db.query(User).filter(User.id == data["id"]).first()
            if msg_type == RABBIT_UPDATE_TYPE:
                if user is None:
                    user = User(
                        id=data["id"],
                        username=data["username"],
                        email=data["email"],
                        name=data["name"],
                        surname=data["surname"],
                        hashed_password=data["hashed_password"],
                        created_at=datetime.fromisoformat(data["created_at"]),
                        updated_at=datetime.fromisoformat(data["updated_at"])
                    )
                    db.add(user)
                    db.commit()
                    logger.error(f"User with id {data['id']} not found during update. Created new user.")
                    return
                user.username = data["username"]
                user.email = data["email"]
                user.name = data["name"]
                user.surname = data["surname"]
                user.hashed_password = data["hashed_password"]
                user.updated_at = datetime.fromisoformat(data["updated_at"])
                db.commit()

            elif msg_type == RABBIT_DELETE_TYPE:
                if user:
                    db.delete(user)
                    db.commit()
                else:
                    logger.error(f"User with id {data['id']} not found during delete.")

            elif msg_type == RABBIT_CREATE_TYPE:
                pass
            else:
                logger.error(f"Unsupported message type: {type}")
        except Exception as e:
            raise OrientatiException(exc=e, url="users/update_from_rabbitMQ")