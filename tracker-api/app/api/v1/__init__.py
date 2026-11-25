from fastapi import APIRouter

from app.api.v1 import items, profile, refresh, topics

router = APIRouter(prefix="/api/v1")
router.include_router(items.router)
router.include_router(topics.router)
router.include_router(profile.router)
router.include_router(refresh.router)
