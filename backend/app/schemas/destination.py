"""
Destination and Seasonal Climate Pydantic Schemas.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any


class SeasonalDataResponse(BaseModel):
    id: int
    destination_id: str
    month: int
    month_name: str
    suitability_score: float
    climate_type: str
    rainfall_level: str
    crowd_demand: str
    water_sports_available: bool
    advisory_notice: Optional[str] = None
    provenance: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)


class DestinationResponse(BaseModel):
    id: str
    name: str
    state: str
    description: str
    latitude: float
    longitude: float
    best_season: str
    hero_image_url: Optional[str] = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class DestinationDetailResponse(DestinationResponse):
    seasonal_records: List[SeasonalDataResponse] = Field(default_factory=list)
    attractions_count: int = 0
