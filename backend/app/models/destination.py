"""
Destination and Seasonal Climate ORM Models.
"""

from typing import List, TYPE_CHECKING
from sqlalchemy import String, Text, Float, Boolean, Integer, JSON, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.attraction import Attraction
    from app.models.trip import Trip


class Destination(Base, TimestampMixin):
    __tablename__ = "destinations"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)  # e.g., "dandeli", "coorg"
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    state: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    best_season: Mapped[str] = mapped_column(String(100), nullable=False)
    hero_image_url: Mapped[str] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    attractions: Mapped[List["Attraction"]] = relationship(
        "Attraction", back_populates="destination", cascade="all, delete-orphan"
    )
    seasonal_records: Mapped[List["SeasonalData"]] = relationship(
        "SeasonalData", back_populates="destination", cascade="all, delete-orphan"
    )
    trips: Mapped[List["Trip"]] = relationship("Trip", back_populates="destination")


class SeasonalData(Base, TimestampMixin):
    __tablename__ = "seasonal_data"
    __table_args__ = (
        UniqueConstraint("destination_id", "month", name="uq_destination_month"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    destination_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("destinations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    month: Mapped[int] = mapped_column(Integer, nullable=False)  # 1 to 12
    month_name: Mapped[str] = mapped_column(String(20), nullable=False)
    suitability_score: Mapped[float] = mapped_column(Float, nullable=False)  # 0.0 to 1.0
    climate_type: Mapped[str] = mapped_column(String(100), nullable=False)
    rainfall_level: Mapped[str] = mapped_column(String(50), nullable=False)  # Low, Moderate, High, Monsoon
    crowd_demand: Mapped[str] = mapped_column(String(50), nullable=False)  # Low, Moderate, High
    water_sports_available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    advisory_notice: Mapped[str] = mapped_column(Text, nullable=True)
    provenance: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    # Relationship
    destination: Mapped["Destination"] = relationship("Destination", back_populates="seasonal_records")
