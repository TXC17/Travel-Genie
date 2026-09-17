"""
Spatial Clustering and Day-Partitioning Pydantic Schemas.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from app.schemas.attraction import AttractionResponse


class ClusterCentroidSchema(BaseModel):
    latitude: float
    longitude: float

    model_config = ConfigDict(from_attributes=True)


class ClusterDaySchema(BaseModel):
    day_number: int = Field(..., description="1-indexed day number corresponding to cluster partition")
    cluster_id: int = Field(..., description="0-indexed cluster identifier")
    attraction_count: int = Field(..., description="Number of attractions allocated to this day")
    centroid: ClusterCentroidSchema = Field(..., description="Geographic centroid of this cluster")
    avg_distance_to_centroid_km: float = Field(..., description="Mean distance of attractions to day centroid in km")
    max_distance_to_centroid_km: float = Field(..., description="Maximum distance of an attraction to day centroid in km")
    dispersion_km: float = Field(..., description="Spatial diameter / dispersion of the cluster in km")
    is_low_utilization: bool = Field(default=False, description="Flag indicating potential low-utilization (e.g. single-attraction day)")
    utilization_note: Optional[str] = Field(default=None, description="Diagnostic message explaining utilization status")
    attractions: List[AttractionResponse] = Field(default_factory=list, description="Attractions assigned to this day")

    model_config = ConfigDict(from_attributes=True)


class ClusteringPartitionRequest(BaseModel):
    destination_id: str = Field(..., description="Destination ID e.g. 'hampi', 'coorg', 'dandeli', 'goa'")
    requested_k: int = Field(..., ge=1, le=14, description="Target number of sightseeing days (K)")
    attraction_ids: Optional[List[str]] = Field(
        default=None,
        description="Explicit list of attraction IDs to partition. If omitted, uses top attractions for destination."
    )
    max_attractions_to_cluster: Optional[int] = Field(
        default=12,
        ge=1,
        le=30,
        description="Maximum number of candidate attractions to partition across days"
    )

    model_config = ConfigDict(from_attributes=True)


class ExcludedAttractionSchema(BaseModel):
    attraction_id: str
    name: str
    reason: str


class ClusteringPartitionResponse(BaseModel):
    destination_id: str
    requested_k: int
    effective_k: int
    is_k_adjusted: bool
    k_adjustment_reason: Optional[str] = None
    total_attractions: int
    total_inertia_km2: float = Field(..., description="Sum of squared Euclidean distances to centroids in projected km^2")
    clusters: List[ClusterDaySchema] = Field(default_factory=list)
    excluded_attractions: List[ExcludedAttractionSchema] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
