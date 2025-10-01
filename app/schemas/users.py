from __future__ import annotations
from pydantic import BaseModel


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str
    access_token: str

class ChangePasswordResponse(BaseModel):
    message: str = "Password changed successfully"
    
class UpdateUserRequest(BaseModel):
    email: str | None = None
    name: str | None = None
    surname: str | None = None
    username: str | None = None
    
class UpdateUserResponse(BaseModel):
    message: str = "User updated successfully"