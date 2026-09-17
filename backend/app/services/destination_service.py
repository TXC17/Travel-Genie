"""
Destination and Seasonality Business Logic Service.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.destination import Destination, SeasonalData
from app.models.attraction import Attraction
from app.schemas.destination import DestinationResponse, DestinationDetailResponse, SeasonalDataResponse
from app.core.exceptions import EntityNotFoundException


class DestinationService:
    @staticmethod
    def get_all_destinations(db: Session, active_only: bool = True) -> List[DestinationResponse]:
        """Fetch all supported destinations."""
        query = db.query(Destination)
        if active_only:
            query = query.filter(Destination.is_active == True)
        destinations = query.order_by(Destination.name).all()
        return [DestinationResponse.model_validate(d) for d in destinations]

    @staticmethod
    def get_destination_by_id(db: Session, destination_id: str) -> DestinationDetailResponse:
        """Fetch a single destination by ID including seasonal curve and attraction counts."""
        dest = db.query(Destination).filter(Destination.id == destination_id).first()
        if not dest:
            raise EntityNotFoundException("Destination", destination_id)

        attractions_count = db.query(Attraction).filter(Attraction.destination_id == destination_id).count()
        seasonal_records = (
            db.query(SeasonalData)
            .filter(SeasonalData.destination_id == destination_id)
            .order_by(SeasonalData.month)
            .all()
        )

        response = DestinationDetailResponse.model_validate(dest)
        response.seasonal_records = [SeasonalDataResponse.model_validate(s) for s in seasonal_records]
        response.attractions_count = attractions_count
        return response

    @staticmethod
    def get_seasonal_records(db: Session, destination_id: str) -> List[SeasonalDataResponse]:
        """Fetch all 12-month climate records for a destination."""
        # Verify destination exists
        dest = db.query(Destination).filter(Destination.id == destination_id).first()
        if not dest:
            raise EntityNotFoundException("Destination", destination_id)

        records = (
            db.query(SeasonalData)
            .filter(SeasonalData.destination_id == destination_id)
            .order_by(SeasonalData.month)
            .all()
        )
        return [SeasonalDataResponse.model_validate(r) for r in records]
