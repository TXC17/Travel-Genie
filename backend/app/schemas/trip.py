"""
Trip and TripPreference Pydantic Schemas.
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from app.schemas.destination import DestinationResponse


class TripPreferenceSchema(BaseModel):
    interests: List[str] = Field(
        default=["nature", "heritage"],
        description="Interest categories e.g. nature, adventure, heritage, coastal, culture_religious"
    )
    pace: str = Field(
        default="Moderate",
        description="Travel intensity pace: Relaxed (6h daily), Moderate (8h daily), Intense (10h daily)"
    )
    preferred_transport: str = Field(
        default="auto",
        description="Preferred transit mode: walking, auto, taxi, rental, public"
    )
    max_daily_travel_hours: float = Field(
        default=4.0,
        ge=1.0,
        le=8.0,
        description="Maximum allowed daily travel/transit hours"
    )
    budget_tier: str = Field(
        default="Standard",
        description="Budget tier: Budget, Standard, Luxury"
    )

    @field_validator("pace")
    @classmethod
    def validate_pace(cls, v: str) -> str:
        valid_paces = ["Relaxed", "Moderate", "Intense"]
        if v not in valid_paces:
            raise ValueError(f"Pace must be one of {valid_paces}")
        return v

    model_config = ConfigDict(from_attributes=True)


class TripCreateRequest(BaseModel):
    destination_id: str = Field(..., description="Target destination ID (e.g. 'coorg', 'dandeli', 'hampi', 'goa')")
    title: Optional[str] = Field(None, description="Custom trip title")
    start_date: str = Field(..., description="Trip start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="Trip end date (YYYY-MM-DD)")
    party_size: int = Field(default=1, ge=1, le=50, description="Number of travelers")
    total_budget: float = Field(..., ge=500.0, description="Total budget in INR")
    preferences: TripPreferenceSchema = Field(default_factory=TripPreferenceSchema)

    @field_validator("start_date", "end_date")
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        try:
            date.fromisoformat(v)
            return v
        except ValueError:
            raise ValueError("Date must be in ISO format YYYY-MM-DD")


class TripUpdateRequest(BaseModel):
    title: Optional[str] = None
    party_size: Optional[int] = Field(None, ge=1, le=50)
    total_budget: Optional[float] = Field(None, ge=500.0)
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    preferences: Optional[TripPreferenceSchema] = None


class TripResponse(BaseModel):
    id: str
    creator_id: str
    destination_id: str
    title: str
    start_date: str
    end_date: str
    number_of_days: int
    party_size: int
    total_budget: float
    status: str
    invite_code: str
    preferences: Optional[TripPreferenceSchema] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TripDetailResponse(TripResponse):
    destination: DestinationResponse
    has_itinerary: bool = False
    latest_itinerary_id: Optional[str] = None
