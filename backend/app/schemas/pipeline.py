"""
Phase 8 Pipeline Diagnostics and Execution Telemetry Pydantic Schemas.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from app.schemas.optimization import MultiDayTripOptimizationResponse, DayOptimizationMetricsSchema
from app.schemas.chat import ExtractedTripConstraintsSchema, ReplanningDiffSchema


class PipelineStageTelemetrySchema(BaseModel):
    stage_name: str
    status: str = "SUCCESS"  # SUCCESS, WARNING, INFEASIBLE, SKIPPED
    duration_ms: float
    details: Dict[str, Any] = Field(default_factory=dict)


class PipelineDiagnosticsSchema(BaseModel):
    pipeline_id: str
    status: str = "COMPLETED"  # COMPLETED, CLARIFICATION_REQUIRED, INFEASIBLE, FAILED
    total_duration_ms: float
    candidate_attractions_count: int = 0
    recommended_attractions_count: int = 0
    clusters_count: int = 0
    total_scheduled_count: int = 0
    total_deferred_count: int = 0
    distance_reduction_pct: float = 0.0
    stages: List[PipelineStageTelemetrySchema] = Field(default_factory=list)
    provenance_classification: str = "computed_diagnostic_telemetry"

    model_config = ConfigDict(from_attributes=True)


class GenerateItineraryRequest(BaseModel):
    destination_id: str
    duration_days: int = Field(default=3, ge=1, le=14)
    total_budget: float = Field(default=15000.0, ge=500.0)
    party_size: int = Field(default=1, ge=1, le=50)
    interests: List[str] = Field(default=["heritage"])
    pace: str = Field(default="Moderate")
    preferred_transport: str = Field(default="auto")
    travel_month: int = Field(default=11, ge=1, le=12)
    start_date: str = Field(default="2026-11-01")

    model_config = ConfigDict(from_attributes=True)


class GenerateItineraryResponse(BaseModel):
    trip_id: str
    itinerary_id: str
    version: int
    title: str
    destination_id: str
    constraints: ExtractedTripConstraintsSchema
    itinerary: MultiDayTripOptimizationResponse
    diagnostics: PipelineDiagnosticsSchema
    explanation: str

    model_config = ConfigDict(from_attributes=True)
