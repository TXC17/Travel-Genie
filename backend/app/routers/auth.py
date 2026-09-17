"""
Authentication Endpoints: Register, Login, and Profile inspection.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    TokenResponse,
    UserResponse,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(request: UserRegisterRequest, db: Session = Depends(get_db)):
    """
    Register a new user account and return a signed JWT access token.
    """
    return AuthService.register_user(db, request)


@router.post("/login", response_model=TokenResponse)
def login(request: UserLoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate with email and password to receive a JWT access token.
    """
    return AuthService.authenticate_user(db, request)


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """
    Get profile information of the currently authenticated user.
    """
    return UserResponse.model_validate(current_user)
