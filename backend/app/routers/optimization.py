"""
Google OR-Tools Route Optimization and Scheduling REST Endpoints.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.optimization import (
    DayOptimizationRequest,
    OptimizedDayScheduleSchema,
    MultiDayTripOptimizationRequest,
    MultiDayTripOptimizationResponse,
)
from app.services.optimization_service import OptimizationService

router = APIRouter(prefix="/optimization", tags=["OR-Tools Route Optimization & Scheduling"])
service = OptimizationService()


@router.post("/optimize-day", response_model=OptimizedDayScheduleSchema)
def optimize_single_day_schedule(
    request: DayOptimizationRequest,
    db: Session = Depends(get_db),
):
    """
    Optimize an intra-day waypoint sequence using Google OR-Tools.
    Validates operating hours, transit times, and pace constraints,
    and returns exact arrival/departure timelines and optimization metrics.
    """
    return service.optimize_day(db, request)


@router.post("/optimize-trip", response_model=MultiDayTripOptimizationResponse)
@router.post("/route", response_model=MultiDayTripOptimizationResponse)
def optimize_multi_day_trip(
    request: MultiDayTripOptimizationRequest,
    db: Session = Depends(get_db),
):
    """
    Optimize a complete multi-day trip from Phase 5 spatial day clusters.
    Computes intra-day TSP routes, validates daily time budgets, and prunes
    lowest-ranked attractions if any day exceeds allowable limits.
    """
    return service.optimize_multi_day_trip(db, request)
