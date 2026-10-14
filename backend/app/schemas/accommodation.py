"""
Accommodation Pydantic Schemas.
Request and response models for accommodation catalog, filtering,
and deterministic budget-aware recommendations with strict date validation
and explicit multi-category budget accounting.
"""

from datetime import date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator


class AccommodationBase(BaseModel):
    id: str = Field(..., description="Unique slug or ID of accommodation")
    destination_id: str = Field(..., description="Destination ID (e.g. dandeli, coorg, hampi, goa)")
    name: str = Field(..., description="Accommodation name")
    accommodation_type: str = Field(..., description="Type: hotel, resort, homestay, hostel, guesthouse")
    category: str = Field(default="Moderate / Mid-Range", description="Ultra-Luxury, Ultra-Budget, or Moderate / Mid-Range")
    description: str = Field(..., description="Overview and setting")
    latitude: float = Field(..., description="Geographical latitude")
    longitude: float = Field(..., description="Geographical longitude")
    price_per_night: float = Field(..., ge=0.0, description="Base double-occupancy nightly rate in INR")
    currency: str = Field(default="INR", description="Currency code")
    rating: Optional[float] = Field(default=None, ge=1.0, le=5.0, description="Guest rating (1.0 to 5.0) or None if unavailable")
    review_count: Optional[int] = Field(default=None, ge=0, description="Documented guest review count, if available")
    room_capacity: int = Field(default=2, ge=1, le=10, description="Standard room guest capacity")
    amenities: List[str] = Field(default_factory=list, description="List of amenities")
    image_url: Optional[str] = Field(None, description="Hero photo URL")
    booking_url: Optional[str] = Field(None, description="Official booking portal or inquiry URL")
    contact_phone: Optional[str] = Field(None, description="Direct phone contact")
    is_verified: bool = Field(default=True, description="True if verified benchmark property")
    provenance: Dict[str, Any] = Field(default_factory=dict, description="Data provenance metadata")
    is_active: bool = Field(default=True, description="Active status")

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def populate_category_and_reviews(cls, values: Any) -> Any:
        if isinstance(values, dict):
            if "category" not in values or not values["category"]:
                prov = values.get("provenance") or {}
                if prov.get("category"):
                    values["category"] = prov["category"]
                else:
                    tier = str(prov.get("rate_tier") or "").lower()
                    price = float(values.get("price_per_night") or 0.0)
                    acc_type = str(values.get("accommodation_type") or "").lower()
                    if tier == "luxury" or price >= 8000:
                        values["category"] = "Ultra-Luxury"
                    elif tier == "budget" or price <= 2600 or (
                        acc_type in ["hostel", "guesthouse"] and price <= 3200
                    ):
                        values["category"] = "Ultra-Budget"
                    else:
                        values["category"] = "Moderate / Mid-Range"
            if "review_count" not in values or values["review_count"] is None:
                prov = values.get("provenance") or {}
                if "review_count" in prov:
                    values["review_count"] = prov["review_count"]
        return values


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
    category: Optional[str] = Field(None, description="Preferred category: 'all', 'ultra_luxury', 'ultra_budget', 'moderate'")
    preferred_type: Optional[str] = Field(None, description="Preferred type: hotel, resort, homestay, hostel, guesthouse")
    required_amenities: Optional[List[str]] = Field(None, description="List of must-have amenities")
    max_price_per_night: Optional[float] = Field(None, ge=0.0, description="Max nightly rate in INR")
    min_rating: Optional[float] = Field(None, ge=1.0, le=5.0, description="Minimum acceptable rating")
    trip_id: Optional[str] = Field(None, description="Optional trip ID to fetch itinerary for location suitability")
    itinerary_id: Optional[str] = Field(None, description="Optional itinerary ID for location suitability")
    itinerary_days: Optional[List[Dict[str, Any]]] = Field(None, description="Optional day schedules with attractions to evaluate multi-day spatial suitability")

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
    category: str = Field(default="Moderate / Mid-Range", description="Accommodation category: Ultra-Luxury, Ultra-Budget, or Moderate / Mid-Range")
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
    is_estimate_complete: bool = False
    booking_note: Optional[str] = Field(None, description="Booking or rate notice")
    location_suitability_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Spatial centralness score across all itinerary days")
    estimated_distance_to_activity_center_km: Optional[float] = Field(None, ge=0.0, description="Estimated road distance from accommodation to itinerary activity centroid in km")
    estimated_total_hotel_transit_km: Optional[float] = Field(None, ge=0.0, description="Total estimated travel between accommodation and daily tour waypoints across all days")
    estimated_daily_hotel_transit_km: Optional[float] = Field(None, ge=0.0, description="Average estimated daily transit distance to/from accommodation")
    estimated_trip_travel_distance_km: Optional[float] = Field(None, ge=0.0, description="Estimated total trip travel distance (sightseeing + hotel transit)")
    location_explanation: Optional[str] = Field(None, description="Explainable spatial proximity assessment")
    distance_reduction_vs_max_km: Optional[float] = Field(None, description="Estimated distance saved compared to least central accommodation")
    provenance_distance_method: Optional[str] = Field(default="haversine_with_road_winding_factor", description="Distance computation method")
    road_winding_factor: Optional[float] = Field(default=1.30, description="Empirical road network winding factor")


class AccommodationBudgetContext(BaseModel):
    total_budget: Optional[float] = None
    allocated_accommodation_budget: Optional[float] = None
    budget_tier: str = "Standard"
    selected_category: str = "All Stays"
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
    is_itinerary_aware: bool = Field(default=False, description="True if recommendations were spatially evaluated against an itinerary")
    total_itinerary_days_evaluated: Optional[int] = Field(None, description="Number of itinerary days evaluated for location suitability")
    activity_center_coordinates: Optional[Dict[str, float]] = Field(None, description="Centroid coordinates of planned itinerary activities (latitude, longitude)")
    category_filter: str = Field(default="all", description="Current category filter applied")
    category_data_status: Optional[str] = Field(None, description="Explanation of dataset depth or missing properties for category")
