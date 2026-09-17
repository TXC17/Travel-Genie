"""
Spatial Clustering and Day-Partitioning REST Endpoints.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.clustering import (
    ClusteringPartitionRequest,
    ClusteringPartitionResponse,
)
from app.services.clustering_service import ClusteringService

router = APIRouter(prefix="/clustering", tags=["Spatial Clustering & Day-Partitioning"])
service = ClusteringService()


@router.post("/partition", response_model=ClusteringPartitionResponse)
def partition_attractions_into_days(
    request: ClusteringPartitionRequest,
    db: Session = Depends(get_db),
):
    """
    Partition eligible attractions into geographically coherent sightseeing days (Day 1..K).
    Applies adaptive K validation and local Equirectangular projection.
    Does NOT perform route sequencing (responsibility of Phase 6 OR-Tools solver).
    """
    return service.partition_attractions(db, request)
