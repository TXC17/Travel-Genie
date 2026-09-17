"""
Trip and TripPreference ORM Models.
"""

import uuid
from typing import List, TYPE_CHECKING
from sqlalchemy import String, Integer, Float, Date, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.destination import Destination
    from app.models.itinerary import Itinerary
    from app.models.collaboration import TripMember, UserVote
    from app.models.chat import ChatSession


class Trip(Base, TimestampMixin):
    __tablename__ = "trips"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    creator_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    destination_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("destinations.id"), nullable=False, index=True
    )

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    start_date: Mapped[str] = mapped_column(String(10), nullable=False)  # "YYYY-MM-DD"
    end_date: Mapped[str] = mapped_column(String(10), nullable=False)    # "YYYY-MM-DD"
    number_of_days: Mapped[int] = mapped_column(Integer, nullable=False)
    party_size: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    total_budget: Mapped[float] = mapped_column(Float, nullable=False)   # in INR

    status: Mapped[str] = mapped_column(String(30), default="draft", nullable=False)  # draft, planned, archived
    invite_code: Mapped[str] = mapped_column(
        String(16), unique=True, index=True, default=lambda: str(uuid.uuid4())[:8].upper()
    )

    # Relationships
    creator: Mapped["User"] = relationship("User", back_populates="created_trips")
    destination: Mapped["Destination"] = relationship("Destination", back_populates="trips")
    preferences: Mapped["TripPreference"] = relationship(
        "TripPreference", back_populates="trip", uselist=False, cascade="all, delete-orphan"
    )
    itineraries: Mapped[List["Itinerary"]] = relationship(
        "Itinerary", back_populates="trip", cascade="all, delete-orphan"
    )
    members: Mapped[List["TripMember"]] = relationship(
        "TripMember", back_populates="trip", cascade="all, delete-orphan"
    )
    votes: Mapped[List["UserVote"]] = relationship(
        "UserVote", back_populates="trip", cascade="all, delete-orphan"
    )
    chat_sessions: Mapped[List["ChatSession"]] = relationship(
        "ChatSession", back_populates="trip", cascade="all, delete-orphan"
    )


class TripPreference(Base, TimestampMixin):
    __tablename__ = "trip_preferences"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    trip_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("trips.id", ondelete="CASCADE"), unique=True, nullable=False
    )

    # Preferences & Constraints
    interests: Mapped[list] = mapped_column(JSON, default=list, nullable=False)  # ["nature", "adventure"]
    pace: Mapped[str] = mapped_column(String(30), default="Moderate", nullable=False)  # Relaxed, Moderate, Intense
    preferred_transport: Mapped[str] = mapped_column(String(30), default="auto", nullable=False)
    max_daily_travel_hours: Mapped[float] = mapped_column(Float, default=4.0, nullable=False)
    budget_tier: Mapped[str] = mapped_column(String(30), default="Standard", nullable=False)

    # Relationship
    trip: Mapped["Trip"] = relationship("Trip", back_populates="preferences")
