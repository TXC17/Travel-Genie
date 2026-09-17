"""
Custom domain and HTTP exceptions for Travel Genie.
"""

from typing import Any, Optional
from fastapi import HTTPException, status


class TravelGenieException(HTTPException):
    """Base application domain exception."""
    def __init__(
        self,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        detail: Any = None,
        headers: Optional[dict] = None,
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)


class EntityNotFoundException(TravelGenieException):
    def __init__(self, entity_name: str, entity_id: Any):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{entity_name} with id '{entity_id}' not found.",
        )


class OptimizationConstraintException(TravelGenieException):
    def __init__(self, message: str, constraints_violated: Optional[dict] = None):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": message,
                "constraints_violated": constraints_violated or {},
            },
        )


class AuthenticationException(TravelGenieException):
    def __init__(self, detail: str = "Could not validate credentials"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class AuthorizationException(TravelGenieException):
    def __init__(self, detail: str = "Not authorized to perform this operation"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )
