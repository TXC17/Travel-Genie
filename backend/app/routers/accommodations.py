"""
Accommodation Recommendation and Catalog Endpoints.
Provides deterministic, explainable accommodation suggestions,
capacity calculations, and budget deduction insights.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.accommodation import (
    AccommodationResponse,
    AccommodationRecommendationRequest,
    AccommodationRecommendationResponse,
)
from app.services.accommodation_service import AccommodationService

router = APIRouter(prefix="/accommodations", tags=["Accommodations"])


@router.get(
    "",
    response_model=List[AccommodationResponse],
    status_code=status.HTTP_200_OK,
    summary="List Accommodations by Destination and Filters",
)
def get_accommodations(
    destination_id: str = Query(..., min_length=2, max_length=50, description="Destination ID (e.g. 'coorg', 'dandeli', 'hampi', 'goa')"),
    budget_tier: Optional[str] = Query(None, description="Filter by tier: Budget, Standard, Luxury"),
    category: Optional[str] = Query(None, description="Filter by category: all, ultra_luxury, ultra_budget, moderate"),
    min_rating: Optional[float] = Query(None, ge=1.0, le=5.0, description="Minimum acceptable rating"),
    max_price_per_night: Optional[float] = Query(None, ge=0.0, description="Maximum nightly rate in INR"),
    accommodation_type: Optional[str] = Query(None, description="Type: hotel, resort, homestay, hostel, guesthouse"),
    db: Session = Depends(get_db),
):
    """Retrieve curated accommodations filtered by destination, price, rating, category, or lodging type."""
    return AccommodationService.get_accommodations_for_destination(
        db=db,
        destination_id=destination_id,
        budget_tier=budget_tier,
        category=category,
        min_rating=min_rating,
        max_price_per_night=max_price_per_night,
        accommodation_type=accommodation_type,
    )


@router.get(
    "/{accommodation_id}",
    response_model=AccommodationResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Accommodation Details by ID",
)
def get_accommodation(
    accommodation_id: str,
    db: Session = Depends(get_db),
):
    """Retrieve full details and provenance metadata for a specific lodging property."""
    result = AccommodationService.get_accommodation_by_id(db=db, accommodation_id=accommodation_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Accommodation with ID '{accommodation_id}' not found.",
        )
    return result


@router.post(
    "/recommendations",
    response_model=AccommodationRecommendationResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Budget-Aware Accommodation Recommendations (JSON Body)",
)
def get_accommodation_recommendations(
    request: AccommodationRecommendationRequest,
    db: Session = Depends(get_db),
):
    """
    Computes deterministic multi-criteria accommodation rankings.
    Analyzes stay nights, required rooms, total stay cost, budget fit score, and transparent match reasons.
    """
    return AccommodationService.get_recommendations(db=db, request=request)


@router.get(
    "/recommendations/query",
    response_model=AccommodationRecommendationResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Budget-Aware Accommodation Recommendations (Query Parameters)",
)
def get_accommodation_recommendations_query(
    destination_id: str = Query(..., description="Destination ID (e.g. 'coorg', 'hampi', 'dandeli', 'goa')"),
    check_in_date: str = Query(..., description="Check-in date YYYY-MM-DD"),
    check_out_date: str = Query(..., description="Check-out date YYYY-MM-DD"),
    party_size: int = Query(1, ge=1, le=50, description="Party size"),
    total_budget: Optional[float] = Query(None, ge=0.0, description="Total trip budget in INR"),
    accommodation_budget: Optional[float] = Query(None, ge=0.0, description="Lodging budget in INR"),
    budget_tier: Optional[str] = Query(None, description="Budget, Standard, Luxury"),
    category: Optional[str] = Query(None, description="all, ultra_luxury, ultra_budget, moderate"),
    preferred_type: Optional[str] = Query(None, description="resort, hotel, homestay, hostel, guesthouse"),
    intercity_transport_cost: Optional[float] = Query(None, ge=0.0, description="Optional intercity transit expense in INR"),
    trip_id: Optional[str] = Query(None, description="Optional trip ID for itinerary location suitability"),
    itinerary_id: Optional[str] = Query(None, description="Optional itinerary ID for itinerary location suitability"),
    db: Session = Depends(get_db),
):
    """Convenience GET endpoint for accommodation recommendations."""
    req = AccommodationRecommendationRequest(
        destination_id=destination_id,
        check_in_date=check_in_date,
        check_out_date=check_out_date,
        party_size=party_size,
        total_budget=total_budget,
        accommodation_budget=accommodation_budget,
        intercity_transport_cost=intercity_transport_cost,
        budget_tier=budget_tier,
        category=category,
        preferred_type=preferred_type,
        trip_id=trip_id,
        itinerary_id=itinerary_id,
    )
    return AccommodationService.get_recommendations(db=db, request=req)
