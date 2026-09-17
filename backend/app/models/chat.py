"""
ChatSession and ChatMessage ORM Models.
"""

import uuid
from typing import List, TYPE_CHECKING
from sqlalchemy import String, Text, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.trip import Trip


class ChatSession(Base, TimestampMixin):
    __tablename__ = "chat_sessions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    trip_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("trips.id", ondelete="CASCADE"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(200), default="Trip Planning Chat", nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="chat_sessions")
    trip: Mapped["Trip"] = relationship("Trip", back_populates="chat_sessions")
    messages: Mapped[List["ChatMessage"]] = relationship(
        "ChatMessage", back_populates="session", cascade="all, delete-orphan"
    )


class ChatMessage(Base, TimestampMixin):
    __tablename__ = "chat_messages"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sender: Mapped[str] = mapped_column(String(20), nullable=False)  # "user", "assistant", "system"
    content: Mapped[str] = mapped_column(Text, nullable=False)
    extracted_constraints: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    # Relationship
    session: Mapped["ChatSession"] = relationship("ChatSession", back_populates="messages")
