"""
Intercity Transportation Recommendation Endpoints.
Provides deterministic, explainable comparison of intercity travel modes
(Car, Bike, Bus, Train, Flight, Boat) with transparent cost and duration estimates.
"""

from typing import Optional
from fastapi import APIRouter, Query, status
from app.schemas.transport import (
    IntercityRecommendationRequest,
    IntercityRecommendationResponse,
)
from app.services.intercity_transport_service import IntercityTransportService

router = APIRouter(prefix="/transport", tags=["Intercity Transportation"])
service = IntercityTransportService()


@router.get(
    "/intercity-recommendations",
    response_model=IntercityRecommendationResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Intercity Travel-Mode Recommendations (Query Parameters)",
    description=(
        "Evaluates Car, Bike, Bus, Train, Flight, and Boat for an intercity journey between origin and destination. "
        "Compares cost, duration, group suitability, and budget compatibility using verified benchmarks "
        "and deterministic multi-criteria scoring."
    ),
)
def get_intercity_recommendations_get(
    origin: str = Query(..., min_length=2, max_length=100, description="Origin city or location (e.g. 'Bengaluru', 'Mumbai')"),
    destination: str = Query(..., min_length=2, max_length=100, description="Destination name or ID (e.g. 'hampi', 'coorg', 'dandeli', 'goa')"),
    party_size: int = Query(1, ge=1, le=50, description="Number of travelers (1 to 50)"),
    budget: Optional[float] = Query(None, ge=0.0, description="Optional total intercity transit budget in INR"),
    user_preferred_mode: Optional[str] = Query(None, description="Optional preferred travel mode (car, bike, bus, train, flight, boat)"),
):
    request = IntercityRecommendationRequest(
        origin=origin,
        destination=destination,
        party_size=party_size,
        budget=budget,
        user_preferred_mode=user_preferred_mode,
    )
    return service.get_recommendations(request)


@router.post(
    "/intercity-recommendations",
    response_model=IntercityRecommendationResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Intercity Travel-Mode Recommendations (JSON Request Body)",
    description="Programmatic JSON endpoint for intercity travel mode recommendations.",
)
def get_intercity_recommendations_post(
    request: IntercityRecommendationRequest,
):
    return service.get_recommendations(request)
