"""
FastAPI Security and Authentication Dependencies.
"""

from typing import Generator, Optional
from fastapi import Depends, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import AuthenticationException
from app.database.session import get_db
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/login", auto_error=False)


def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Extract and validate JWT Bearer token, returning the authenticated User.
    Raises 401 AuthenticationException if token is missing, invalid, or expired.
    """
    if not token:
        raise AuthenticationException("Not authenticated. Bearer token required.")

    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise AuthenticationException("Invalid token payload: subject missing.")
    except JWTError:
        raise AuthenticationException("Could not validate credentials or token expired.")

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise AuthenticationException("User account not found.")

    if not user.is_active:
        raise AuthenticationException("User account is inactive.")

    return user
