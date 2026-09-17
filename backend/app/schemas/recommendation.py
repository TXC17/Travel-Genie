"""
Recommendation and MCDM Scoring Pydantic Schemas.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Optional, Any
from app.schemas.attraction import AttractionResponse


class MCDMWeightsSchema(BaseModel):
    weight_interest: float = Field(default=0.35, ge=0.0, le=1.0)
    weight_season: float = Field(default=0.25, ge=0.0, le=1.0)
    weight_popularity: float = Field(default=0.15, ge=0.0, le=1.0)
    weight_rating: float = Field(default=0.15, ge=0.0, le=1.0)
    weight_budget: float = Field(default=0.10, ge=0.0, le=1.0)

    model_config = ConfigDict(from_attributes=True)


class ScoreBreakdown(BaseModel):
    interest_score: float
    season_score: float
    popularity_score: float
    rating_score: float
    budget_score: float
    composite_score: float
    reason: str


class ScoredAttractionResponse(BaseModel):
    attraction: AttractionResponse
    composite_score: float
    rank: int
    breakdown: ScoreBreakdown
    weights_used: MCDMWeightsSchema

    model_config = ConfigDict(from_attributes=True)


class RecommendationRequest(BaseModel):
    destination_id: str
    travel_month: int = Field(..., ge=1, le=12, description="Month of travel (1-12)")
    interests: List[str] = Field(default=["nature", "heritage"])
    total_budget: float = Field(default=15000.0, ge=500.0)
    number_of_days: int = Field(default=3, ge=1, le=14)
    party_size: int = Field(default=1, ge=1, le=50)
    custom_weights: Optional[MCDMWeightsSchema] = None


class DestinationSeasonalComparisonItem(BaseModel):
    destination_id: str
    destination_name: str
    state: str
    month: int
    month_name: str
    suitability_score: float
    climate_type: str
    rainfall_level: str
    crowd_demand: str
    water_sports_available: bool
    advisory_notice: Optional[str] = None
    is_recommended: bool


class SeasonalComparisonResponse(BaseModel):
    selected_destination_id: Optional[str] = None
    travel_month: int
    travel_month_name: str
    destinations_ranked: List[DestinationSeasonalComparisonItem]
    better_alternatives_available: bool
    recommendation_summary: str
