"""
Pydantic Schemas for Intercity Transportation Recommendations.
Defines transparent schemas for comparing Car, Bike, Bus, Train, Flight, and Boat
with explicit provenance, verification status, and budget compatibility.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict


class TransportModeEnum(str, Enum):
    CAR = "car"
    BIKE = "bike"
    BUS = "bus"
    TRAIN = "train"
    FLIGHT = "flight"
    BOAT = "boat"


class VerificationStatusEnum(str, Enum):
    VERIFIED = "VERIFIED"
    ESTIMATED = "ESTIMATED"
    UNAVAILABLE = "UNAVAILABLE"


class BudgetCompatibilityEnum(str, Enum):
    WITHIN_BUDGET = "WITHIN_BUDGET"
    OVER_BUDGET = "OVER_BUDGET"
    NOT_SPECIFIED = "NOT_SPECIFIED"


class IntercityOptionSchema(BaseModel):
    transport_mode: TransportModeEnum
    mode_name: str
    origin: str
    destination: str
    is_available: bool = True
    unavailability_reason: Optional[str] = None

    # Distance information with explicit provenance distinction
    distance_km: Optional[float] = None
    distance_type: str = Field(
        ...,
        description="verified_road, verified_rail, straight_line_air, estimated_road_winding, or unavailable"
    )

    # Duration and Cost
    estimated_duration_hours: Optional[float] = None
    estimated_cost_per_person: Optional[float] = None
    estimated_total_cost: Optional[float] = None
    cost_per_km: Optional[float] = None

    # Group Suitability & Capacity
    group_suitability_score: float = Field(ge=0.0, le=1.0)
    group_suitability_label: str = "Moderate"
    group_suitability_notes: str

    # Budget & Ranking
    budget_compatibility: BudgetCompatibilityEnum = BudgetCompatibilityEnum.NOT_SPECIFIED
    score: float = Field(ge=0.0, le=1.0)
    rank: int = Field(ge=1)
    recommendation_reason: str

    # Trade-off Analysis
    advantages: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)

    # Provenance
    verification_status: VerificationStatusEnum = VerificationStatusEnum.ESTIMATED
    data_provenance: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)


class IntercityRecommendationRequest(BaseModel):
    origin: str = Field(..., min_length=2, max_length=100, description="Departure city or location")
    destination: str = Field(..., min_length=2, max_length=100, description="Destination city, code, or name")
    party_size: int = Field(default=1, ge=1, le=50, description="Number of travelers")
    budget: Optional[float] = Field(default=None, ge=0.0, description="Total budget in INR allocated for intercity travel")
    user_preferred_mode: Optional[str] = Field(default=None, description="Optional user preferred travel mode")

    @field_validator("origin", "destination")
    @classmethod
    def strip_and_validate_non_empty(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("Location string cannot be empty or whitespace.")
        return clean

    model_config = ConfigDict(from_attributes=True)


class IntercityRecommendationResponse(BaseModel):
    origin: str
    destination: str
    destination_id: Optional[str] = None
    party_size: int
    budget: Optional[float] = None
    fastest_mode: Optional[str] = None
    cheapest_mode: Optional[str] = None
    best_ranked_mode: Optional[str] = None
    options: List[IntercityOptionSchema] = Field(default_factory=list)
    available_count: int = 0
    methodology_summary: str

    model_config = ConfigDict(from_attributes=True)
