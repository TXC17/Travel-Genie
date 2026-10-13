"""
Accommodation Pydantic Schemas.
Request and response models for accommodation catalog, filtering,
and deterministic budget-aware recommendations with strict date validation
and explicit multi-category budget accounting.
"""

from datetime import date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict, field_validator


class AccommodationBase(BaseModel):
    id: str = Field(..., description="Unique slug or ID of accommodation")
    destination_id: str = Field(..., description="Destination ID (e.g. dandeli, coorg, hampi, goa)")
    name: str = Field(..., description="Accommodation name")
    accommodation_type: str = Field(..., description="Type: hotel, resort, homestay, hostel, guesthouse")
    description: str = Field(..., description="Overview and setting")
    latitude: float = Field(..., description="Geographical latitude")
    longitude: float = Field(..., description="Geographical longitude")
    price_per_night: float = Field(..., ge=0.0, description="Base double-occupancy nightly rate in INR")
    currency: str = Field(default="INR", description="Currency code")
    rating: float = Field(default=4.0, ge=1.0, le=5.0, description="Guest rating (1.0 to 5.0)")
    room_capacity: int = Field(default=2, ge=1, le=10, description="Standard room guest capacity")
    amenities: List[str] = Field(default_factory=list, description="List of amenities")
    image_url: Optional[str] = Field(None, description="Hero photo URL")
    booking_url: Optional[str] = Field(None, description="Official booking portal or inquiry URL")
    contact_phone: Optional[str] = Field(None, description="Direct phone contact")
    is_verified: bool = Field(default=True, description="True if verified benchmark property")
    provenance: Dict[str, Any] = Field(default_factory=dict, description="Data provenance metadata")
    is_active: bool = Field(default=True, description="Active status")

    model_config = ConfigDict(from_attributes=True)


class AccommodationResponse(AccommodationBase):
    pass


class AccommodationRecommendationRequest(BaseModel):
    destination_id: str = Field(..., description="Target destination ID (e.g. 'coorg', 'dandeli', 'hampi', 'goa')")
    check_in_date: str = Field(..., description="Check-in date (YYYY-MM-DD)")
    check_out_date: str = Field(..., description="Check-out date (YYYY-MM-DD)")
    party_size: int = Field(default=1, ge=1, le=50, description="Number of travelers")
    total_budget: Optional[float] = Field(None, ge=0.0, description="Total overall trip budget in INR")
    accommodation_budget: Optional[float] = Field(None, ge=0.0, description="Specific budget allocated to accommodation in INR")
    intercity_transport_cost: Optional[float] = Field(None, ge=0.0, description="Optional intercity transit cost already accounted for in INR")
    budget_tier: Optional[str] = Field(None, description="Preferred tier: Budget, Standard, Luxury")
    preferred_type: Optional[str] = Field(None, description="Preferred type: hotel, resort, homestay, hostel, guesthouse")
    required_amenities: Optional[List[str]] = Field(None, description="List of must-have amenities")
    max_price_per_night: Optional[float] = Field(None, ge=0.0, description="Max nightly rate in INR")
    min_rating: Optional[float] = Field(None, ge=1.0, le=5.0, description="Minimum acceptable rating")

    @field_validator("check_in_date", "check_out_date")
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        try:
            date.fromisoformat(v)
            return v
        except (ValueError, TypeError):
            raise ValueError("Date must be in ISO format YYYY-MM-DD")

    @field_validator("check_out_date")
    @classmethod
    def validate_checkout_after_checkin(cls, v: str, info) -> str:
        check_in = info.data.get("check_in_date")
        if check_in:
            try:
                d_in = date.fromisoformat(check_in)
                d_out = date.fromisoformat(v)
                if d_out <= d_in:
                    raise ValueError(
                        "check_out_date must be strictly after check_in_date (stay must include at least one night)"
                    )
            except ValueError as e:
                if "check_out_date must be strictly after" in str(e):
                    raise
        return v


class AccommodationRecommendationItem(BaseModel):
    accommodation: AccommodationResponse
    nights: int = Field(..., ge=1, description="Number of nights stayed")
    rooms_needed: int = Field(..., ge=1, description="Number of rooms required for group based on property capacity")
    price_per_night: float = Field(..., description="Nightly rate per room in INR")
    total_cost: float = Field(..., description="Total stay cost: nights * price_per_night * rooms_needed")
    intercity_transport_cost: Optional[float] = Field(None, description="Intercity transit cost included in total accounted expenses")
    total_accounted_cost: float = Field(..., description="Total expenses accounted for (accommodation + optional intercity transit)")
    budget_fit_score: float = Field(..., ge=0.0, le=1.0, description="Budget suitability score")
    remaining_budget: Optional[float] = Field(None, description="Remaining trip budget after all accounted costs in INR")
    remaining_budget_after_accommodation: Optional[float] = Field(None, description="Remaining budget strictly after accommodation expense in INR")
    budget_utilization_pct: Optional[float] = Field(None, description="Percentage of total trip budget utilized by accounted costs")
    is_within_budget: bool = Field(..., description="True if total_cost is within the allocated lodging budget")
    match_score: float = Field(..., ge=0.0, le=1.0, description="Multi-criteria composite match score (0.0 to 1.0)")
    match_reasons: List[str] = Field(default_factory=list, description="Explainable reasons for recommendation")
    provenance_badge: str = Field(default="VERIFIED", description="VERIFIED, ESTIMATED, or UNAVAILABLE")
    included_cost_categories: List[str] = Field(default_factory=list, description="Cost categories deducted from budget")
    excluded_cost_categories: List[str] = Field(default_factory=list, description="Cost categories not yet deducted from budget")
    is_estimate_complete: bool = Field(default=False, description="False if admissions, food, or local transport are excluded")
    booking_note: Optional[str] = Field(None, description="Booking or rate notice")


class AccommodationBudgetContext(BaseModel):
    total_budget: Optional[float] = None
    allocated_accommodation_budget: Optional[float] = None
    budget_tier: str = "Standard"
    nights: int = 1
    party_size: int = 1
    rooms_needed: int = 1
    standard_double_rooms_estimate: int = 1
    intercity_transport_cost: Optional[float] = None
    total_accounted_cost: Optional[float] = None
    included_cost_categories: List[str] = Field(default_factory=list)
    excluded_cost_categories: List[str] = Field(default_factory=list)
    is_estimate_complete: bool = False


class AccommodationRecommendationResponse(BaseModel):
    destination_id: str
    destination_name: str
    check_in_date: str
    check_out_date: str
    nights: int
    party_size: int
    rooms_needed: int
    budget_context: AccommodationBudgetContext
    recommendations: List[AccommodationRecommendationItem]
    summary: str
