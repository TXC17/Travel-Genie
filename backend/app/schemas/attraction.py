"""
Attraction and Category Pydantic Schemas.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any


class AttractionCategoryResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    icon_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class AttractionResponse(BaseModel):
    id: str
    destination_id: str
    category: str
    category_id: Optional[str] = None
    name: str
    description: str
    latitude: float
    longitude: float
    average_visit_duration: float
    entry_fee: float = 0.0
    popularity_score: Optional[float] = 0.5
    rating: Optional[float] = 4.0
    opening_time: Optional[str] = None
    closing_time: Optional[str] = None
    best_time_to_visit: Optional[str] = None
    tags: Optional[List[str]] = Field(default_factory=list)
    seasonal_scores: Optional[Dict[str, float]] = Field(default_factory=dict)
    crowd_heuristics: Optional[Dict[str, Any]] = Field(default_factory=dict)
    provenance: Optional[Dict[str, Any]] = Field(default_factory=dict)
    is_verified: Optional[bool] = False
    duration_estimation_method: Optional[str] = "curated_empirical_average"

    model_config = ConfigDict(from_attributes=True)


class AttractionFilterParams(BaseModel):
    destination_id: Optional[str] = None
    category: Optional[str] = None
    min_rating: Optional[float] = None
    max_entry_fee: Optional[float] = None
    query: Optional[str] = None
