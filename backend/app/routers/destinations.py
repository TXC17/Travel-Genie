"""
Destination and Seasonal Analytics Endpoints.
"""

from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.destination import (
    DestinationResponse,
    DestinationDetailResponse,
    SeasonalDataResponse,
)
from app.services.destination_service import DestinationService

router = APIRouter(prefix="/destinations", tags=["Destinations"])


@router.get("", response_model=List[DestinationResponse])
def get_destinations(db: Session = Depends(get_db)):
    """
    List all supported tourist destinations.
    """
    return DestinationService.get_all_destinations(db)


@router.get("/{destination_id}", response_model=DestinationDetailResponse)
def get_destination(destination_id: str, db: Session = Depends(get_db)):
    """
    Get destination metadata, seasonal climate curve, and total attraction counts.
    """
    return DestinationService.get_destination_by_id(db, destination_id)


@router.get("/{destination_id}/seasonal", response_model=List[SeasonalDataResponse])
def get_destination_seasonal_data(destination_id: str, db: Session = Depends(get_db)):
    """
    Get 12-month climate normals, suitability scores, and weather advisories.
    """
    return DestinationService.get_seasonal_records(db, destination_id)
