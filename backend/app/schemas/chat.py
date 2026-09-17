"""
Conversational AI, Constraint Extraction, and Smart Replanning Pydantic Schemas.
"""

from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any, Union
from app.schemas.optimization import MultiDayTripOptimizationResponse


class ExtractedTripConstraintsSchema(BaseModel):
    destination_id: Optional[str] = Field(
        default=None, description="Extracted destination ID (e.g. 'hampi', 'coorg', 'dandeli', 'goa')"
    )
    destination_name: Optional[str] = None
    duration_days: Optional[int] = Field(
        default=None, ge=1, le=14, description="Target number of sightseeing days"
    )
    total_budget: Optional[float] = Field(
        default=None, ge=0.0, description="Total budget in INR"
    )
    party_size: Optional[int] = Field(
        default=None, ge=1, le=50, description="Number of travelers"
    )
    interests: Optional[List[str]] = Field(
        default=None, description="Extracted interest tags, e.g. ['heritage', 'nature', 'adventure']"
    )
    pace: Optional[str] = Field(
        default=None, description="Travel pace: 'Relaxed', 'Moderate', or 'Intense'"
    )
    preferred_transport: Optional[str] = Field(
        default=None, description="'walking', 'auto', 'car', 'taxi', 'rental', or 'public'"
    )
    start_date: Optional[str] = Field(
        default=None, description="Start date in YYYY-MM-DD"
    )
    travel_month: Optional[int] = Field(
        default=None, ge=1, le=12, description="1-indexed travel month"
    )
    max_daily_travel_hours: Optional[float] = Field(
        default=None, ge=1.0, le=16.0, description="Max daily travel/sightseeing hours"
    )
    budget_tier: Optional[str] = Field(
        default=None, description="'budget', 'standard', or 'luxury'"
    )
    is_complete: bool = Field(
        default=False, description="True if destination and duration are identified"
    )
    missing_fields: List[str] = Field(
        default_factory=list, description="List of essential fields still missing"
    )
    clarification_question: Optional[str] = Field(
        default=None, description="Suggested question to clarify underspecified requirements"
    )
    extraction_method: str = Field(
        default="rule_based_fallback", description="'gemini_nlu' or 'rule_based_fallback'"
    )

    model_config = ConfigDict(from_attributes=True)


class ConstraintChangeItemSchema(BaseModel):
    field: str
    old_value: Any
    new_value: Any


class RemovedAttractionItemSchema(BaseModel):
    attraction_id: str
    name: str
    reason: str


class AddedAttractionItemSchema(BaseModel):
    attraction_id: str
    name: str
    day_number: int
    reason: str


class MovedAttractionItemSchema(BaseModel):
    attraction_id: str
    name: str
    from_day: int
    to_day: int


class ReplanningDiffSchema(BaseModel):
    is_replanned: bool = False
    changed_constraints: List[ConstraintChangeItemSchema] = Field(default_factory=list)
    removed_attractions: List[RemovedAttractionItemSchema] = Field(default_factory=list)
    added_attractions: List[AddedAttractionItemSchema] = Field(default_factory=list)
    moved_attractions: List[MovedAttractionItemSchema] = Field(default_factory=list)
    distance_change_km: float = 0.0
    travel_time_change_hours: float = 0.0
    budget_change: float = 0.0
    reasoning: List[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class ChatMessageSchema(BaseModel):
    id: str
    session_id: str
    sender: str
    content: str
    extracted_constraints: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ChatSessionSchema(BaseModel):
    id: str
    user_id: str
    trip_id: Optional[str] = None
    title: str
    created_at: Optional[datetime] = None
    messages: List[ChatMessageSchema] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class ChatSessionCreateRequest(BaseModel):
    title: Optional[str] = Field(default="Trip Planning Chat", max_length=200)
    trip_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class SendMessageRequest(BaseModel):
    content: str = Field(..., min_length=1, description="Natural language user request")

    model_config = ConfigDict(from_attributes=True)


class SendMessageResponse(BaseModel):
    session_id: str
    message_id: str
    sender: str = "assistant"
    content: str
    extracted_constraints: ExtractedTripConstraintsSchema
    itinerary: Optional[MultiDayTripOptimizationResponse] = None
    persisted_itinerary_id: Optional[str] = None
    replanning_diff: Optional[ReplanningDiffSchema] = None
    is_clarification: bool = False
    clarification_question: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
