"""
Authentication and User Pydantic Schemas.
"""

from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import datetime
from typing import Optional


class UserRegisterRequest(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=6, description="Password (min 6 characters)")
    full_name: str = Field(..., min_length=2, max_length=100, description="Full name")


class UserLoginRequest(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class UserResponse(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
