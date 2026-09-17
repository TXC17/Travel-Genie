"""
SQLAlchemy ORM Models Registry.
Exports all models for Alembic migrations and Base.metadata.create_all().
"""

from app.database.base import Base
from app.models.user import User
from app.models.destination import Destination, SeasonalData
from app.models.attraction import AttractionCategory, Attraction
from app.models.trip import Trip, TripPreference
from app.models.itinerary import Itinerary, ItineraryDay, ItineraryItem
from app.models.collaboration import TripMember, UserVote
from app.models.chat import ChatSession, ChatMessage

__all__ = [
    "Base",
    "User",
    "Destination",
    "SeasonalData",
    "AttractionCategory",
    "Attraction",
    "Trip",
    "TripPreference",
    "Itinerary",
    "ItineraryDay",
    "ItineraryItem",
    "TripMember",
    "UserVote",
    "ChatSession",
    "ChatMessage",
]
