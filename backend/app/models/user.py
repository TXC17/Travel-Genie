"""
User ORM Model.
"""

import uuid
from typing import List, TYPE_CHECKING
from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.trip import Trip
    from app.models.collaboration import TripMember, UserVote
    from app.models.chat import ChatSession


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    created_trips: Mapped[List["Trip"]] = relationship(
        "Trip", back_populates="creator", cascade="all, delete-orphan"
    )
    memberships: Mapped[List["TripMember"]] = relationship(
        "TripMember", back_populates="user", cascade="all, delete-orphan"
    )
    votes: Mapped[List["UserVote"]] = relationship(
        "UserVote", back_populates="user", cascade="all, delete-orphan"
    )
    chat_sessions: Mapped[List["ChatSession"]] = relationship(
        "ChatSession", back_populates="user", cascade="all, delete-orphan"
    )
