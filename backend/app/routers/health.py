"""
Health check and diagnostic routes.
"""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.config import settings
from app.database.session import get_db
from app.schemas.health import HealthCheckResponse

router = APIRouter(tags=["Health & System"])


@router.get("/health", response_model=HealthCheckResponse)
def get_health_status(db: Session = Depends(get_db)):
    """
    Check system health status, runtime configuration, and database connectivity.
    """
    db_status = "connected"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return HealthCheckResponse(
        status="healthy" if db_status == "connected" else "degraded",
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        timestamp=datetime.now(timezone.utc),
        environment=settings.ENVIRONMENT,
        database=db_status,
    )
