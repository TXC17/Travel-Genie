"""
Attraction and Category ORM Models with Provenance Tracking.
"""

import uuid
from typing import List, TYPE_CHECKING
from sqlalchemy import String, Text, Float, Boolean, JSON, ForeignKey, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.destination import Destination
    from app.models.itinerary import ItineraryItem
    from app.models.collaboration import UserVote


class AttractionCategory(Base, TimestampMixin):
    __tablename__ = "attraction_categories"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)  # e.g., "adventure", "heritage"
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    icon_name: Mapped[str] = mapped_column(String(50), nullable=True)

    # Relationships
    attractions: Mapped[List["Attraction"]] = relationship("Attraction", back_populates="category_rel")


class Attraction(Base, TimestampMixin):
    __tablename__ = "attractions"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)  # e.g., "dandeli_kali_rafting"
    destination_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("destinations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    category_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("attraction_categories.id"), nullable=True
    )

    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)

    # Operational & Visit Attributes
    average_visit_duration: Mapped[float] = mapped_column(Float, nullable=False)  # in hours (e.g. 1.5)
    entry_fee: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)  # in INR
    popularity_score: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)  # 0.0 to 1.0
    rating: Mapped[float] = mapped_column(Float, default=4.0, nullable=False)  # 1.0 to 5.0

    opening_time: Mapped[str] = mapped_column(String(10), nullable=True)  # "09:00:00"
    closing_time: Mapped[str] = mapped_column(String(10), nullable=True)  # "17:30:00"
    best_time_to_visit: Mapped[str] = mapped_column(String(100), nullable=True)  # "Morning", "Sunset"

    # Multi-attribute weights & heuristic parameters
    tags: Mapped[list] = mapped_column(JSON, default=list, nullable=False)  # ["nature", "rafting"]
    seasonal_scores: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)  # {"1": 1.0, ...}
    crowd_heuristics: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    # Provenance, Verification, and Estimation Metadata
    provenance: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    duration_estimation_method: Mapped[str] = mapped_column(
        String(100), default="curated_empirical_average", nullable=False
    )

    # Relationships
    destination: Mapped["Destination"] = relationship("Destination", back_populates="attractions")
    category_rel: Mapped["AttractionCategory"] = relationship("AttractionCategory", back_populates="attractions")
    itinerary_items: Mapped[List["ItineraryItem"]] = relationship(
        "ItineraryItem", back_populates="attraction"
    )
    user_votes: Mapped[List["UserVote"]] = relationship(
        "UserVote", back_populates="attraction", cascade="all, delete-orphan"
    )
