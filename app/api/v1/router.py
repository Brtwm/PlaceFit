"""API v1 router."""

from fastapi import APIRouter

from app.api.v1.endpoints import analyze, compare, competitors, geocode, locations

router = APIRouter()

router.include_router(analyze.router)
router.include_router(compare.router)
router.include_router(locations.router)
router.include_router(geocode.router)
router.include_router(competitors.router)
