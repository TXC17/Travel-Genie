"""
Trip Collaboration and Member Voting ORM Models.
"""

import uuid
from typing import TYPE_CHECKING
from sqlalchemy import String, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.trip import Trip
    from app.models.attraction import Attraction


class TripMember(Base, TimestampMixin):
    __tablename__ = "trip_members"
    __table_args__ = (
        UniqueConstraint("trip_id", "user_id", name="uq_trip_member"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    trip_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("trips.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(20), default="member", nullable=False)  # owner, editor, member

    # Relationships
    trip: Mapped["Trip"] = relationship("Trip", back_populates="members")
    user: Mapped["User"] = relationship("User", back_populates="memberships")


class UserVote(Base, TimestampMixin):
    __tablename__ = "user_votes"
    __table_args__ = (
        UniqueConstraint("trip_id", "user_id", "attraction_id", name="uq_user_attraction_vote"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    trip_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("trips.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    attraction_id: Mapped[str] = mapped_column(
        String(100), ForeignKey("attractions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    vote_value: Mapped[int] = mapped_column(Integer, default=1, nullable=False)  # +1 (upvote), -1 (downvote)

    # Relationships
    trip: Mapped["Trip"] = relationship("Trip", back_populates="votes")
    user: Mapped["User"] = relationship("User", back_populates="votes")
    attraction: Mapped["Attraction"] = relationship("Attraction", back_populates="user_votes")
