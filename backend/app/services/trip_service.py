"""
Trip and Preference Management Business Logic Service.
"""

from datetime import date
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.trip import Trip, TripPreference
from app.models.destination import Destination
from app.models.collaboration import TripMember
from app.schemas.trip import (
    TripCreateRequest,
    TripUpdateRequest,
    TripResponse,
    TripDetailResponse,
    TripPreferenceSchema,
)
from app.schemas.destination import DestinationResponse
from app.core.exceptions import EntityNotFoundException, TravelGenieException


class TripService:
    @staticmethod
    def calculate_trip_days(start_date_str: str, end_date_str: str) -> int:
        """Calculate number of sightseeing days inclusive."""
        d_start = date.fromisoformat(start_date_str)
        d_end = date.fromisoformat(end_date_str)
        if d_end < d_start:
            raise TravelGenieException(
                status_code=400,
                detail="End date cannot be prior to start date."
            )
        days = (d_end - d_start).days + 1
        if days > 14:
            raise TravelGenieException(
                status_code=400,
                detail="Maximum supported trip duration is 14 days."
            )
        return days

    @staticmethod
    def create_trip(db: Session, user_id: str, request: TripCreateRequest) -> TripResponse:
        """Create a new trip along with nested preferences."""
        # 1. Validate destination exists
        dest = db.query(Destination).filter(Destination.id == request.destination_id).first()
        if not dest:
            raise EntityNotFoundException("Destination", request.destination_id)

        # 2. Compute duration
        num_days = TripService.calculate_trip_days(request.start_date, request.end_date)

        # 3. Generate default title if none provided
        title = request.title or f"{num_days}-Day Trip to {dest.name}"

        new_trip = Trip(
            creator_id=user_id,
            destination_id=request.destination_id,
            title=title,
            start_date=request.start_date,
            end_date=request.end_date,
            number_of_days=num_days,
            party_size=request.party_size,
            total_budget=request.total_budget,
            status="draft",
        )

        # Attach preferences
        prefs_data = request.preferences
        pref = TripPreference(
            interests=prefs_data.interests,
            pace=prefs_data.pace,
            preferred_transport=prefs_data.preferred_transport,
            max_daily_travel_hours=prefs_data.max_daily_travel_hours,
            budget_tier=prefs_data.budget_tier,
        )
        new_trip.preferences = pref

        # Add creator as owner in trip members table
        member = TripMember(user_id=user_id, role="owner")
        new_trip.members.append(member)

        db.add(new_trip)
        db.commit()
        db.refresh(new_trip)

        response = TripResponse.model_validate(new_trip)
        response.preferences = TripPreferenceSchema.model_validate(new_trip.preferences)
        return response

    @staticmethod
    def get_user_trips(db: Session, user_id: str) -> List[TripResponse]:
        """Fetch all trips created by or shared with a user."""
        trips = (
            db.query(Trip)
            .filter(Trip.creator_id == user_id)
            .order_by(Trip.created_at.desc())
            .all()
        )
        result = []
        for t in trips:
            resp = TripResponse.model_validate(t)
            if t.preferences:
                resp.preferences = TripPreferenceSchema.model_validate(t.preferences)
            result.append(resp)
        return result

    @staticmethod
    def get_trip_by_id(db: Session, trip_id: str, user_id: Optional[str] = None) -> TripDetailResponse:
        """Fetch full trip detail by ID."""
        trip = db.query(Trip).filter(Trip.id == trip_id).first()
        if not trip:
            raise EntityNotFoundException("Trip", trip_id)

        response = TripDetailResponse(
            id=trip.id,
            creator_id=trip.creator_id,
            destination_id=trip.destination_id,
            title=trip.title,
            start_date=trip.start_date,
            end_date=trip.end_date,
            number_of_days=trip.number_of_days,
            party_size=trip.party_size,
            total_budget=trip.total_budget,
            status=trip.status,
            invite_code=trip.invite_code,
            preferences=TripPreferenceSchema.model_validate(trip.preferences) if trip.preferences else None,
            destination=DestinationResponse.model_validate(trip.destination),
            has_itinerary=len(trip.itineraries) > 0,
            latest_itinerary_id=trip.itineraries[0].id if trip.itineraries else None,
            created_at=trip.created_at,
        )
        return response

    @staticmethod
    def update_trip_preferences(
        db: Session, trip_id: str, user_id: str, request: TripUpdateRequest
    ) -> TripResponse:
        """Update constraints and preferences for an existing trip."""
        trip = db.query(Trip).filter(Trip.id == trip_id).first()
        if not trip:
            raise EntityNotFoundException("Trip", trip_id)

        if trip.creator_id != user_id:
            raise TravelGenieException(status_code=403, detail="Not authorized to edit this trip.")

        if request.title:
            trip.title = request.title
        if request.party_size:
            trip.party_size = request.party_size
        if request.total_budget:
            trip.total_budget = request.total_budget

        if request.start_date and request.end_date:
            trip.start_date = request.start_date
            trip.end_date = request.end_date
            trip.number_of_days = TripService.calculate_trip_days(request.start_date, request.end_date)

        if request.preferences:
            if not trip.preferences:
                trip.preferences = TripPreference(trip_id=trip.id)
            trip.preferences.interests = request.preferences.interests
            trip.preferences.pace = request.preferences.pace
            trip.preferences.preferred_transport = request.preferences.preferred_transport
            trip.preferences.max_daily_travel_hours = request.preferences.max_daily_travel_hours
            trip.preferences.budget_tier = request.preferences.budget_tier

        db.commit()
        db.refresh(trip)

        response = TripResponse.model_validate(trip)
        response.preferences = TripPreferenceSchema.model_validate(trip.preferences)
        return response

    @staticmethod
    def delete_trip(db: Session, trip_id: str, user_id: str) -> None:
        """Delete a trip by ID."""
        trip = db.query(Trip).filter(Trip.id == trip_id).first()
        if not trip:
            raise EntityNotFoundException("Trip", trip_id)
        if trip.creator_id != user_id:
            raise TravelGenieException(status_code=403, detail="Not authorized to delete this trip.")

        db.delete(trip)
        db.commit()
