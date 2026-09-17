"""
Main FastAPI Application Entrypoint.
Initializes middleware, CORS, routers, and application lifecycle.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.exceptions import TravelGenieException
from app.database.base import Base
from app.database.session import engine
from app.routers.api_v1 import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    # Create tables if not exist (especially for local development/sqlite)
    Base.metadata.create_all(bind=engine)
    yield
    # Cleanup on shutdown if needed


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-Driven System for Optimized Travel Itinerary Generation",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure Cross-Origin Resource Sharing (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(TravelGenieException)
async def travel_genie_exception_handler(request: Request, exc: TravelGenieException):
    """Custom exception handler for domain exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=exc.headers,
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Fallback handler for uncaught server errors."""
    if settings.DEBUG:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": f"Internal Server Error: {str(exc)}"},
        )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred."},
    )


# Mount central API v1 router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/", tags=["Root"])
def root_redirect():
    """Root redirect to API documentation."""
    return {
        "project": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "api_v1": settings.API_V1_PREFIX,
        "status": "online",
    }
