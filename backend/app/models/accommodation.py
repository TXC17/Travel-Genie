"""
Accommodation ORM Model.
Represents verified lodging options with pricing, amenities, room capacity,
and transparent provenance metadata.
"""

from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import String, Text, Float, Boolean, Integer, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.destination import Destination
    from app.models.trip import Trip


class Accommodation(Base, TimestampMixin):
    __tablename__ = "accommodations"

    id: Mapped[str] = mapped_column(String(60), primary_key=True)
    destination_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("destinations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    accommodation_type: Mapped[str] = mapped_column(String(50), nullable=False)  # resort, hotel, homestay, hostel, guesthouse
    description: Mapped[str] = mapped_column(Text, nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    price_per_night: Mapped[float] = mapped_column(Float, nullable=False)  # Base room rate in INR
    currency: Mapped[str] = mapped_column(String(10), default="INR", nullable=False)
    rating: Mapped[Optional[float]] = mapped_column(Float, default=None, nullable=True)
    room_capacity: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    amenities: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    booking_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    contact_phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    provenance: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    destination: Mapped["Destination"] = relationship("Destination", back_populates="accommodations")
    trips: Mapped[List["Trip"]] = relationship("Trip", back_populates="selected_accommodation")

    @property
    def category(self) -> str:
        """Classify into Ultra-Luxury, Ultra-Budget, or Moderate / Mid-Range."""
        prov = self.provenance if isinstance(self.provenance, dict) else {}
        if prov.get("category"):
            return str(prov["category"])
        tier = str(prov.get("rate_tier") or "").lower()
        if tier == "luxury" or self.price_per_night >= 8000:
            return "Ultra-Luxury"
        if tier == "budget" or self.price_per_night <= 2600 or (
            self.accommodation_type in ["hostel", "guesthouse"] and self.price_per_night <= 3200
        ):
            return "Ultra-Budget"
        return "Moderate / Mid-Range"

    @property
    def review_count(self) -> Optional[int]:
        """Documented review count from provenance metadata, if available."""
        prov = self.provenance if isinstance(self.provenance, dict) else {}
        return prov.get("review_count")
