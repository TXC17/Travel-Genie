"""
Itinerary, ItineraryDay, and ItineraryItem ORM Models.
"""

import uuid
from typing import List, TYPE_CHECKING
from sqlalchemy import String, Integer, Float, Boolean, Text, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.trip import Trip
    from app.models.attraction import Attraction


class Itinerary(Base, TimestampMixin):
    __tablename__ = "itineraries"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    trip_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("trips.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_current: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Aggregated Summary Metrics
    total_estimated_cost: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_travel_distance_km: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_travel_duration_hours: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_sightseeing_duration_hours: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Academic Optimization Performance Benchmark Stats
    optimization_metrics: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    explanation_summary: Mapped[str] = mapped_column(Text, nullable=True)

    # Relationships
    trip: Mapped["Trip"] = relationship("Trip", back_populates="itineraries")
    days: Mapped[List["ItineraryDay"]] = relationship(
        "ItineraryDay", back_populates="itinerary", cascade="all, delete-orphan"
    )


class ItineraryDay(Base, TimestampMixin):
    __tablename__ = "itinerary_days"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    itinerary_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("itineraries.id", ondelete="CASCADE"), nullable=False, index=True
    )
    day_number: Mapped[int] = mapped_column(Integer, nullable=False)  # 1, 2, 3...
    date: Mapped[str] = mapped_column(String(10), nullable=False)     # "YYYY-MM-DD"
    cluster_id: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Day-wise Calculated Metrics
    day_travel_distance_km: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    day_travel_duration_hours: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    day_sightseeing_duration_hours: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    day_estimated_cost: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Transport Recommendation for the Day
    recommended_transport: Mapped[str] = mapped_column(String(50), nullable=False)
    transport_reason: Mapped[str] = mapped_column(Text, nullable=True)

    # Relationships
    itinerary: Mapped["Itinerary"] = relationship("Itinerary", back_populates="days")
    items: Mapped[List["ItineraryItem"]] = relationship(
        "ItineraryItem", back_populates="itinerary_day", cascade="all, delete-orphan"
    )


class ItineraryItem(Base, TimestampMixin):
    __tablename__ = "itinerary_items"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    itinerary_day_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("itinerary_days.id", ondelete="CASCADE"), nullable=False, index=True
    )
    attraction_id: Mapped[str] = mapped_column(
        String(100), ForeignKey("attractions.id"), nullable=False, index=True
    )

    visit_order: Mapped[int] = mapped_column(Integer, nullable=False)  # 1, 2, 3...
    arrival_time: Mapped[str] = mapped_column(String(10), nullable=False)    # "09:30"
    departure_time: Mapped[str] = mapped_column(String(10), nullable=False)  # "11:30"
    visit_duration_hours: Mapped[float] = mapped_column(Float, nullable=False)

    # Leg transit info from previous waypoint
    travel_time_from_prev_hours: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    distance_from_prev_km: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    item_cost: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Crowd Density Estimate Indicator
    crowd_estimate_score: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    crowd_level: Mapped[str] = mapped_column(String(20), default="Moderate", nullable=False)
    visit_notes: Mapped[str] = mapped_column(Text, nullable=True)

    # Relationships
    itinerary_day: Mapped["ItineraryDay"] = relationship("ItineraryDay", back_populates="items")
    attraction: Mapped["Attraction"] = relationship("Attraction", back_populates="itinerary_items")
