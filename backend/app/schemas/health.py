"""Health check schemas."""
from datetime import datetime
from pydantic import BaseModel, Field


class HealthCheckResponse(BaseModel):
    status: str = Field(..., description="Service status", json_schema_extra={"example": "healthy"})
    app_name: str = Field(..., description="Application name")
    version: str = Field(..., description="Application version")
    timestamp: datetime = Field(..., description="Current server time")
    environment: str = Field(..., description="Deployment environment")
    database: str = Field(..., description="Database connection status")
