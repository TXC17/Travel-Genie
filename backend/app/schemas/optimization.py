"""
Route Optimization and Constraint Scheduling Pydantic Schemas.
Defines waypoint visit schedules, travel legs, optimization savings metrics,
and deferred attraction records with explicit provenance and feasibility metadata.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from app.schemas.attraction import AttractionResponse
from app.schemas.clustering import ClusterDaySchema


class RouteLegSchema(BaseModel):
    from_attraction_id: str
    from_attraction_name: str
    to_attraction_id: str
    to_attraction_name: str
    distance_km: float
    travel_time_hours: float
    transport_mode: str
    estimated_transit_cost: float
    provenance_method: str = "haversine_with_road_winding_factor"
    provenance_classification: str = "computed_estimate"

    model_config = ConfigDict(from_attributes=True)


class ScheduledVisitItemSchema(BaseModel):
    attraction: AttractionResponse
    visit_order: int
    arrival_time: str = Field(..., description="Estimated arrival time (HH:MM)")
    departure_time: str = Field(..., description="Estimated departure time (HH:MM)")
    visit_duration_hours: float
    travel_time_from_prev_hours: float = 0.0
    distance_from_prev_km: float = 0.0
    item_admission_fee: float = 0.0
    waiting_time_hours: float = 0.0
    crowd_estimate_score: float = 0.5
    crowd_level: str = "Moderate"
    visit_notes: Optional[str] = None
    provenance_classification: str = "computed_schedule"

    model_config = ConfigDict(from_attributes=True)


class DayOptimizationMetricsSchema(BaseModel):
    original_route_distance_km: float
    optimized_route_distance_km: float
    distance_reduction_km: float
    distance_reduction_pct: float
    original_travel_time_hours: float
    optimized_travel_time_hours: float
    travel_time_reduction_hours: float
    solver_status: str = "OPTIMAL"
    objective_function: str = "minimize_total_intra_day_road_distance"

    model_config = ConfigDict(from_attributes=True)


class DeferredAttractionSchema(BaseModel):
    attraction_id: str
    attraction_name: str
    original_day_number: int
    reason: str
    violating_constraint: str = Field(
        ...,
        description="Type of constraint exceeded: daily_time_limit, opening_hours, closing_hours, or visit_duration"
    )
    mcdm_score: Optional[float] = None
    provenance_classification: str = "computed_pruning_decision"

    model_config = ConfigDict(from_attributes=True)


class OptimizedDayScheduleSchema(BaseModel):
    day_number: int
    date: Optional[str] = None
    cluster_id: int
    attraction_count: int
    feasibility_status: str = Field(
        default="FEASIBLE",
        description="FEASIBLE, FEASIBLE_AFTER_PRUNING, or INFEASIBLE_ALL_PRUNED"
    )
    recommended_transport: str = "auto"
    day_start_time: str = "09:00"
    day_end_time: str = "17:00"
    total_sightseeing_duration_hours: float
    total_travel_duration_hours: float
    total_waiting_duration_hours: float
    total_day_duration_hours: float
    total_travel_distance_km: float
    day_estimated_admission_cost: float
    day_estimated_transit_cost: float
    day_total_estimated_cost: float
    route_sequence: List[int] = Field(default_factory=list, description="0-indexed visit permutation order")
    ordered_attractions: List[AttractionResponse] = Field(default_factory=list, description="Sequenced attractions")
    optimization_metrics: DayOptimizationMetricsSchema
    items: List[ScheduledVisitItemSchema] = Field(default_factory=list)
    legs: List[RouteLegSchema] = Field(default_factory=list)
    constraint_violations: List[str] = Field(default_factory=list)
    provenance_metadata: Dict[str, Any] = Field(
        default_factory=lambda: {
            "distance_model": "haversine_with_road_winding_factor",
            "road_winding_factor": 1.30,
            "provenance_classification": "computed_estimate",
        }
    )

    model_config = ConfigDict(from_attributes=True)


class DayOptimizationRequest(BaseModel):
    destination_id: str
    trip_id: Optional[str] = None
    day_number: int = 1
    cluster: ClusterDaySchema
    preferred_transport: str = Field(default="auto", description="walking, auto, car, taxi, rental, public")
    pace: str = Field(default="Moderate", description="Relaxed (6h limit), Moderate (8h limit), Intense (10h limit)")
    day_start_time: str = Field(default="09:00", description="Start time in HH:MM")
    mcdm_scores_map: Optional[Dict[str, float]] = Field(
        default=None,
        description="Optional precomputed MCDM score per attraction ID for priority pruning"
    )

    model_config = ConfigDict(from_attributes=True)


class MultiDayTripOptimizationRequest(BaseModel):
    destination_id: str
    trip_id: Optional[str] = None
    clusters: List[ClusterDaySchema]
    start_date: str = Field(default="2026-11-01", description="Trip start date (YYYY-MM-DD)")
    preferred_transport: str = Field(default="auto")
    pace: str = Field(default="Moderate")
    day_start_time: str = Field(default="09:00")
    total_budget: float = Field(default=15000.0, ge=500.0)
    party_size: int = Field(default=1, ge=1, le=50)
    mcdm_scores_map: Optional[Dict[str, float]] = Field(default=None)

    model_config = ConfigDict(from_attributes=True)


class MultiDayTripOptimizationResponse(BaseModel):
    destination_id: str
    trip_id: Optional[str] = None
    total_days: int
    total_scheduled_attractions: int
    total_deferred_attractions: int
    total_travel_distance_km: float
    total_travel_duration_hours: float
    total_sightseeing_duration_hours: float
    total_day_duration_hours: float
    total_estimated_cost: float
    aggregate_distance_reduction_pct: float
    days: List[OptimizedDayScheduleSchema] = Field(default_factory=list)
    deferred_attractions: List[DeferredAttractionSchema] = Field(default_factory=list)
    provenance_metadata: Dict[str, Any] = Field(
        default_factory=lambda: {
            "distance_model": "haversine_with_road_winding_factor",
            "road_winding_factor": 1.30,
            "solver": "google_ortools_with_held_karp_fallback",
            "provenance_classification": "computed_estimate",
        }
    )

    model_config = ConfigDict(from_attributes=True)
