"""
Main API v1 router - combines all endpoint routers
"""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, users, artworks, spaces, ai, uploads

# Create main API router
api_router = APIRouter()

# Include sub-routers
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"]
)

api_router.include_router(
    users.router,
    prefix="/users",
    tags=["Users"]
)

api_router.include_router(
    artworks.router,
    prefix="/artworks",
    tags=["Artworks"]
)

api_router.include_router(
    spaces.router,
    prefix="/spaces",
    tags=["Spaces"]
)

api_router.include_router(
    ai.router,
    prefix="/ai",
    tags=["AI & ML"]
)

api_router.include_router(
    uploads.router,
    prefix="/uploads",
    tags=["File Uploads"]
)
