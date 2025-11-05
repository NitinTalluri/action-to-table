from fastapi import APIRouter
from .deliverables import router as deliverables_router
from .completions import router as completions_router
from .time_tracking import router as time_tracking_router

router = APIRouter()

router.include_router(deliverables_router)
router.include_router(completions_router, prefix="/completions")
router.include_router(time_tracking_router, prefix="/time_tracking")
