"""
Route Optimization and Constraint Scheduling Service.
Integrates OR-Tools route optimizer with trip records, database attractions, and preferences.
"""

from typing import List, Optional, Dict
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
from app.core.exceptions import EntityNotFoundException


class OptimizationService:
    def __init__(self):
        self.optimizer = IntraDayRouteOptimizer()
        self.clusterer = SpatialDayClusterer()

    def optimize_day(
        self, db: Session, request: DayOptimizationRequest
    ) -> OptimizedDayScheduleSchema:
        """
        Optimize a single day cluster's itinerary route and timeline schedule.
        """
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

        return self.optimizer.optimize_multi_day_trip(request)
