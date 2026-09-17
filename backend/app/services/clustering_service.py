"""
Clustering Business Logic Service.
Coordinates database queries with the SpatialDayClusterer engine.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.attraction import Attraction
from app.models.destination import Destination
from app.algorithms.clustering import SpatialDayClusterer
from app.schemas.clustering import (
    ClusteringPartitionRequest,
    ClusteringPartitionResponse,
)
from app.core.exceptions import EntityNotFoundException


class ClusteringService:
    def __init__(self):
        self.clusterer = SpatialDayClusterer()

    def partition_attractions(
        self, db: Session, request: ClusteringPartitionRequest
    ) -> ClusteringPartitionResponse:
        """
        Partition tourist attractions for a destination into geographic day clusters.
        """
        # 1. Verify destination exists
        dest = db.query(Destination).filter(Destination.id == request.destination_id).first()
        if not dest:
            raise EntityNotFoundException("Destination", request.destination_id)

        # 2. Fetch candidate attractions
        if request.attraction_ids:
            attractions = (
                db.query(Attraction)
                .filter(Attraction.destination_id == request.destination_id)
                .filter(Attraction.id.in_(request.attraction_ids))
                .all()
            )
        else:
            limit = request.max_attractions_to_cluster or 12
            attractions = (
                db.query(Attraction)
                .filter(Attraction.destination_id == request.destination_id)
                .order_by(Attraction.popularity_score.desc())
                .limit(limit)
                .all()
            )

        # 3. Execute Spatial K-Means Day Partitioning
        return self.clusterer.partition_days(
            destination_id=request.destination_id,
            attractions=attractions,
            requested_k=request.requested_k,
        )
