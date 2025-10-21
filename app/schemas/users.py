from __future__ import annotations
from pydantic import BaseModel

from app.services.http_client import OrientatiResponse


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

class ChangePasswordResponse(OrientatiResponse):
    def __init__(self):
        message = "Password changed successfully"
        super().__init__(status_code=200, data={"message": message})
    
class UpdateUserRequest(BaseModel):
    email: str | None = None
    name: str | None = None
    surname: str | None = None
    username: str | None = None
    
class UpdateUserResponse(OrientatiResponse):
    def __init__(self):
        message = "User updated successfully"
        super().__init__(status_code=200, data={"message": message})
    
class DeleteUserResponse(OrientatiResponse):
    def __init__(self):
        message = "User deleted successfully"
        super().__init__(status_code=200, data={"message": message})