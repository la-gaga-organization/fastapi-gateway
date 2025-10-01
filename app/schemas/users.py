from __future__ import annotations
from pydantic import BaseModel


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

class ChangePasswordResponse(BaseModel):
    message: str = "Password changed successfully"