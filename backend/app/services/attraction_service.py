"""
Attraction and Category Query Service.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.attraction import Attraction, AttractionCategory
from app.schemas.attraction import (
    AttractionResponse,
    AttractionCategoryResponse,
    AttractionFilterParams,
)
from app.core.exceptions import EntityNotFoundException


class AttractionService:
    @staticmethod
    def get_categories(db: Session) -> List[AttractionCategoryResponse]:
        """Fetch all attraction categories."""
        categories = db.query(AttractionCategory).order_by(AttractionCategory.name).all()
        return [AttractionCategoryResponse.model_validate(c) for c in categories]

    @staticmethod
    def filter_attractions(
        db: Session, filters: AttractionFilterParams
    ) -> List[AttractionResponse]:
        """Filter attractions by destination, category, rating, fee, or keyword."""
        query = db.query(Attraction)

        if filters.destination_id:
            query = query.filter(Attraction.destination_id == filters.destination_id)

        if filters.category:
            query = query.filter(
                or_(
                    Attraction.category == filters.category,
                    Attraction.category_id == filters.category,
                )
            )

        if filters.min_rating is not None:
            query = query.filter(Attraction.rating >= filters.min_rating)

        if filters.max_entry_fee is not None:
            query = query.filter(Attraction.entry_fee <= filters.max_entry_fee)

        if filters.query:
            search_pattern = f"%{filters.query}%"
            query = query.filter(
                or_(
                    Attraction.name.ilike(search_pattern),
                    Attraction.description.ilike(search_pattern),
                )
            )

        attractions = query.order_by(Attraction.popularity_score.desc()).all()
        return [AttractionResponse.model_validate(a) for a in attractions]

    @staticmethod
    def get_attraction_by_id(db: Session, attraction_id: str) -> AttractionResponse:
        """Fetch a single attraction by its unique ID."""
        attr = db.query(Attraction).filter(Attraction.id == attraction_id).first()
        if not attr:
            raise EntityNotFoundException("Attraction", attraction_id)
        return AttractionResponse.model_validate(attr)
