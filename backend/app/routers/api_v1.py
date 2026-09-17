"""
Central API v1 Router.
Aggregates all feature endpoints under /api/v1.
"""

from fastapi import APIRouter
from app.routers import health, auth, destinations, attractions, trips, recommendations, clustering, optimization, chat

api_router = APIRouter()

# Register core endpoints
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(destinations.router)
api_router.include_router(attractions.router)
api_router.include_router(trips.router)
api_router.include_router(recommendations.router)
api_router.include_router(clustering.router)
api_router.include_router(optimization.router)
api_router.include_router(chat.router)

# Future algorithm routers:
# - collaboration (group voting, conflict resolution)
