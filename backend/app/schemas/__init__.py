"""
Pydantic Schemas Registry.
"""

from app.schemas.health import HealthCheckResponse
from app.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    UserResponse,
    TokenResponse,
)
from app.schemas.destination import (
    DestinationResponse,
    DestinationDetailResponse,
    SeasonalDataResponse,
)
from app.schemas.attraction import (
    AttractionCategoryResponse,
    AttractionResponse,
    AttractionFilterParams,
)
from app.schemas.trip import (
    TripPreferenceSchema,
    TripCreateRequest,
    TripUpdateRequest,
    TripResponse,
    TripDetailResponse,
)
from app.schemas.recommendation import (
    MCDMWeightsSchema,
    ScoreBreakdown,
    ScoredAttractionResponse,
    RecommendationRequest,
    DestinationSeasonalComparisonItem,
    SeasonalComparisonResponse,
)
from app.schemas.clustering import (
    ClusterCentroidSchema,
    ClusterDaySchema,
    ClusteringPartitionRequest,
    ExcludedAttractionSchema,
    ClusteringPartitionResponse,
)
from app.schemas.optimization import (
    RouteLegSchema,
    ScheduledVisitItemSchema,
    DayOptimizationMetricsSchema,
    DeferredAttractionSchema,
    OptimizedDayScheduleSchema,
    DayOptimizationRequest,
    MultiDayTripOptimizationRequest,
    MultiDayTripOptimizationResponse,
)
from app.schemas.chat import (
    ExtractedTripConstraintsSchema,
    ConstraintChangeItemSchema,
    RemovedAttractionItemSchema,
    AddedAttractionItemSchema,
    MovedAttractionItemSchema,
    ReplanningDiffSchema,
    ChatMessageSchema,
    ChatSessionSchema,
    ChatSessionCreateRequest,
    SendMessageRequest,
    SendMessageResponse,
)
from app.schemas.pipeline import (
    PipelineStageTelemetrySchema,
    PipelineDiagnosticsSchema,
    GenerateItineraryRequest,
    GenerateItineraryResponse,
)

__all__ = [
    "HealthCheckResponse",
    "UserRegisterRequest",
    "UserLoginRequest",
    "UserResponse",
    "TokenResponse",
    "DestinationResponse",
    "DestinationDetailResponse",
    "SeasonalDataResponse",
    "AttractionCategoryResponse",
    "AttractionResponse",
    "AttractionFilterParams",
    "TripPreferenceSchema",
    "TripCreateRequest",
    "TripUpdateRequest",
    "TripResponse",
    "TripDetailResponse",
    "MCDMWeightsSchema",
    "ScoreBreakdown",
    "ScoredAttractionResponse",
    "RecommendationRequest",
    "DestinationSeasonalComparisonItem",
    "SeasonalComparisonResponse",
    "ClusterCentroidSchema",
    "ClusterDaySchema",
    "ClusteringPartitionRequest",
    "ExcludedAttractionSchema",
    "ClusteringPartitionResponse",
    "RouteLegSchema",
    "ScheduledVisitItemSchema",
    "DayOptimizationMetricsSchema",
    "DeferredAttractionSchema",
    "OptimizedDayScheduleSchema",
    "DayOptimizationRequest",
    "MultiDayTripOptimizationRequest",
    "MultiDayTripOptimizationResponse",
    "ExtractedTripConstraintsSchema",
    "ConstraintChangeItemSchema",
    "RemovedAttractionItemSchema",
    "AddedAttractionItemSchema",
    "MovedAttractionItemSchema",
    "ReplanningDiffSchema",
    "ChatMessageSchema",
    "ChatSessionSchema",
    "ChatSessionCreateRequest",
    "SendMessageRequest",
    "SendMessageResponse",
    "PipelineStageTelemetrySchema",
    "PipelineDiagnosticsSchema",
    "GenerateItineraryRequest",
    "GenerateItineraryResponse",
]
