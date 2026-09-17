"""
Recommendation Business Logic Service.
Coordinates MCDM Recommender and Seasonal Analyzer algorithms with database queries.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.attraction import Attraction
from app.models.destination import Destination
from app.algorithms.recommender import MCDMRecommender
from app.algorithms.seasonal_analyzer import SeasonalAnalyzer
from app.schemas.recommendation import (
    RecommendationRequest,
    ScoredAttractionResponse,
    SeasonalComparisonResponse,
    MCDMWeightsSchema,
)
from app.core.exceptions import EntityNotFoundException


class RecommendationService:
    def __init__(self):
        self.recommender = MCDMRecommender()

    def get_ranked_attractions(
        self, db: Session, request: RecommendationRequest
    ) -> List[ScoredAttractionResponse]:
        """Rank attractions within a destination based on MCDM scoring."""
        # 1. Verify destination
        dest = db.query(Destination).filter(Destination.id == request.destination_id).first()
        if not dest:
            raise EntityNotFoundException("Destination", request.destination_id)

        # 2. Query candidate attractions for destination
        attractions = (
            db.query(Attraction)
            .filter(Attraction.destination_id == request.destination_id)
            .all()
        )

        # 3. Apply MCDM Recommender ranking
        return self.recommender.rank_attractions(attractions, request)

    def compare_seasons(
        self, db: Session, travel_month: int, destination_id: Optional[str] = None
    ) -> SeasonalComparisonResponse:
        """Compare climate suitability across all destinations for month M."""
        return SeasonalAnalyzer.compare_destinations_by_month(
            db, travel_month, destination_id
        )

    @staticmethod
    def get_default_weights() -> MCDMWeightsSchema:
        """Return the baseline MCDM weights for sensitivity inspection."""
        return MCDMWeightsSchema()
