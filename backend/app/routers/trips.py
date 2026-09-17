"""
Trip Management and Preference Endpoints.
"""

from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.trip import (
    TripCreateRequest,
    TripUpdateRequest,
    TripResponse,
    TripDetailResponse,
)
from app.schemas.pipeline import (
    GenerateItineraryRequest,
    GenerateItineraryResponse,
)
from app.services.trip_service import TripService
from app.services.pipeline_service import PlanningPipelineService

router = APIRouter(prefix="/trips", tags=["Trips"])
pipeline_service = PlanningPipelineService()


@router.post("/generate-itinerary", response_model=GenerateItineraryResponse, status_code=status.HTTP_201_CREATED)
def generate_and_persist_itinerary(
    request: GenerateItineraryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Execute the complete deterministic planning pipeline (MCDM -> K-Means -> OR-Tools -> Persistence)
    and return the optimized multi-day itinerary with execution diagnostics.
    """
    return pipeline_service.generate_itinerary(db, str(current_user.id), request)


@router.post("", response_model=TripResponse, status_code=status.HTTP_201_CREATED)
def create_trip(
    request: TripCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a new trip planning session with destination, dates, budget, and travel preferences.
    """
    return TripService.create_trip(db, current_user.id, request)


@router.get("", response_model=List[TripResponse])
def get_user_trips(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List all trips created by the currently authenticated user.
    """
    return TripService.get_user_trips(db, current_user.id)


@router.get("/{trip_id}", response_model=TripDetailResponse)
def get_trip(
    trip_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get full trip details, destination metadata, and preference constraints.
    """
    return TripService.get_trip_by_id(db, trip_id, current_user.id)


@router.put("/{trip_id}/preferences", response_model=TripResponse)
def update_trip_preferences(
    trip_id: str,
    request: TripUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update trip preferences or boundary constraints (e.g. party size, budget, pace, dates).
    """
    return TripService.update_trip_preferences(db, trip_id, current_user.id, request)


@router.delete("/{trip_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_trip(
    trip_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Delete a trip by ID.
    """
    TripService.delete_trip(db, trip_id, current_user.id)
