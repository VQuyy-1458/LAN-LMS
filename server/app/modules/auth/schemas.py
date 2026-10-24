"""TV1: password input is never echoed by response models."""
from typing import Literal
from pydantic import BaseModel, Field


class Login(BaseModel):
    username: str = Field(min_length=1, max_length=128)
    password: str = Field(min_length=1, max_length=128)


class ChangePassword(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


class UserResponse(BaseModel):
    user_id: int
    username: str
    role: Literal['teacher', 'student']
    must_change_password: bool


class LoginResponse(BaseModel):
    user: UserResponse


class CsrfResponse(BaseModel):
    csrf_token: str
