"""
Authentication Business Logic Service.
Handles registration, credentials validation, and JWT token issuance.
"""

from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.auth import UserRegisterRequest, UserLoginRequest, TokenResponse, UserResponse
from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.exceptions import TravelGenieException, AuthenticationException


class AuthService:
    @staticmethod
    def register_user(db: Session, request: UserRegisterRequest) -> TokenResponse:
        """Register a new user account and return an access token."""
        # Check if email is already taken
        existing_user = db.query(User).filter(User.email == request.email).first()
        if existing_user:
            raise TravelGenieException(
                status_code=409,
                detail=f"An account with email '{request.email}' already exists."
            )

        new_user = User(
            email=request.email,
            hashed_password=get_password_hash(request.password),
            full_name=request.full_name,
            is_active=True,
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        token = create_access_token(subject=new_user.id)
        return TokenResponse(
            access_token=token,
            token_type="bearer",
            user=UserResponse.model_validate(new_user),
        )

    @staticmethod
    def authenticate_user(db: Session, request: UserLoginRequest) -> TokenResponse:
        """Validate user credentials and return an access token."""
        user = db.query(User).filter(User.email == request.email).first()
        if not user or not verify_password(request.password, user.hashed_password):
            raise AuthenticationException("Invalid email or password.")

        if not user.is_active:
            raise AuthenticationException("Account is deactivated.")

        token = create_access_token(subject=user.id)
        return TokenResponse(
            access_token=token,
            token_type="bearer",
            user=UserResponse.model_validate(user),
        )
