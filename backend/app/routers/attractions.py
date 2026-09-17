"""
Attraction Query and Category Endpoints.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.attraction import (
    AttractionResponse,
    AttractionCategoryResponse,
    AttractionFilterParams,
)
from app.services.attraction_service import AttractionService

router = APIRouter(prefix="/attractions", tags=["Attractions"])


@router.get("/categories", response_model=List[AttractionCategoryResponse])
def get_categories(db: Session = Depends(get_db)):
    """
    List all normalized attraction categories.
    """
    return AttractionService.get_categories(db)


@router.get("", response_model=List[AttractionResponse])
def get_attractions(
    destination_id: Optional[str] = Query(None, description="Filter by destination ID"),
    category: Optional[str] = Query(None, description="Filter by category ID"),
    min_rating: Optional[float] = Query(None, ge=1.0, le=5.0, description="Minimum star rating"),
    max_entry_fee: Optional[float] = Query(None, ge=0.0, description="Maximum entry fee in INR"),
    query: Optional[str] = Query(None, description="Keyword text search in name/description"),
    db: Session = Depends(get_db),
):
    """
    Filter and query points of interest with verified coordinates and operational metadata.
    """
    filters = AttractionFilterParams(
        destination_id=destination_id,
        category=category,
        min_rating=min_rating,
        max_entry_fee=max_entry_fee,
        query=query,
    )
    return AttractionService.filter_attractions(db, filters)


@router.get("/{attraction_id}", response_model=AttractionResponse)
def get_attraction(attraction_id: str, db: Session = Depends(get_db)):
    """
    Get full metadata for a specific attraction including provenance citations.
    """
    return AttractionService.get_attraction_by_id(db, attraction_id)
