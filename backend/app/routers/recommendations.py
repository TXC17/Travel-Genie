"""
Recommendation Endpoints: Multi-Criteria Decision Making (MCDM) Scoring & Seasonal Comparison.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.recommendation import (
    RecommendationRequest,
    ScoredAttractionResponse,
    SeasonalComparisonResponse,
    MCDMWeightsSchema,
)
from app.services.recommendation_service import RecommendationService

router = APIRouter(prefix="/recommendations", tags=["Recommendations & Analytics"])
service = RecommendationService()


@router.post("/attractions", response_model=List[ScoredAttractionResponse])
def get_attraction_recommendations(
    request: RecommendationRequest,
    db: Session = Depends(get_db),
):
    """
    Rank destination attractions using Explainable Multi-Criteria Decision Making (MCDM).
    Returns composite score, ranking, component breakdown, and transparent attribution reasons.
    """
    return service.get_ranked_attractions(db, request)


@router.get("/seasonal-compare", response_model=SeasonalComparisonResponse)
@router.get("/destinations/seasonal-comparison", response_model=SeasonalComparisonResponse)
def compare_seasonal_suitability(
    travel_month: Optional[int] = Query(None, ge=1, le=12, description="Month of travel (1-12)"),
    month: Optional[int] = Query(None, ge=1, le=12, description="Month of travel (1-12) alias"),
    destination_id: Optional[str] = Query(None, description="Optional target destination to evaluate"),
    db: Session = Depends(get_db),
):
    """
    Compare seasonal climate, weather alerts, and suitability across all supported destinations.
    """
    effective_month = travel_month if travel_month is not None else (month if month is not None else 11)
    return service.compare_seasons(db, effective_month, destination_id)


@router.get("/weights", response_model=MCDMWeightsSchema)
def get_default_mcdm_weights():
    """
    Get baseline MCDM criteria weights (interest, season, popularity, rating, budget).
    """
    return service.get_default_weights()
