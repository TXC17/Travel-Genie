"""
Route Optimization and Constraint Scheduling Service.
Integrates OR-Tools route optimizer with trip records, database attractions, and preferences.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.destination import Destination
from app.models.trip import Trip
from app.algorithms.route_optimizer import IntraDayRouteOptimizer
from app.algorithms.clustering import SpatialDayClusterer
from app.schemas.optimization import (
    DayOptimizationRequest,
    OptimizedDayScheduleSchema,
    MultiDayTripOptimizationRequest,
    MultiDayTripOptimizationResponse,
    DeferredAttractionSchema,
)
from app.core.exceptions import EntityNotFoundException, OptimizationConstraintException
from app.models.accommodation import Accommodation


class OptimizationService:
    def __init__(self):
        self.optimizer = IntraDayRouteOptimizer()
        self.clusterer = SpatialDayClusterer()

    def _validate_accommodation_endpoint(
        self, db: Session, destination_id: str, endpoint: Optional[Any]
    ) -> None:
        """
        Validate that if an accommodation endpoint is provided and exists in database,
        it is active and its destination matches the requested destination.
        """
        if not endpoint or not getattr(endpoint, "id", None):
            return

        acc = db.query(Accommodation).filter(Accommodation.id == endpoint.id).first()
        if acc:
            if not acc.is_active:
                raise OptimizationConstraintException(
                    f"Selected accommodation '{acc.name}' is inactive and cannot be used for routing.",
                    {"accommodation_id": acc.id, "is_active": False},
                )
            if acc.destination_id.lower() != destination_id.lower():
                raise OptimizationConstraintException(
                    f"Accommodation '{acc.name}' belongs to destination '{acc.destination_id}', "
                    f"which does not match the requested destination '{destination_id}'.",
                    {
                        "accommodation_destination_id": acc.destination_id,
                        "requested_destination_id": destination_id,
                    },
                )

    def optimize_day(
        self, db: Session, request: DayOptimizationRequest
    ) -> OptimizedDayScheduleSchema:
        """
        Optimize a single day cluster's itinerary route and timeline schedule.
        """
        dest = db.query(Destination).filter(Destination.id == request.destination_id).first()
        if not dest:
            raise EntityNotFoundException("Destination", request.destination_id)

        if request.accommodation:
            self._validate_accommodation_endpoint(db, request.destination_id, request.accommodation)

        schedule, _ = self.optimizer.optimize_day_schedule(request)
        return schedule

    def optimize_multi_day_trip(
        self, db: Session, request: MultiDayTripOptimizationRequest
    ) -> MultiDayTripOptimizationResponse:
        """
        Optimize full multi-day trip using provided spatial day clusters.
        """
        # Validate destination exists
        dest = db.query(Destination).filter(Destination.id == request.destination_id).first()
        if not dest:
            raise EntityNotFoundException("Destination", request.destination_id)

        if request.accommodation:
            self._validate_accommodation_endpoint(db, request.destination_id, request.accommodation)

        return self.optimizer.optimize_multi_day_trip(request)
