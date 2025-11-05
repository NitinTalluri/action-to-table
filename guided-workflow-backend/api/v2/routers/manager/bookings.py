from fastapi import APIRouter

from .bookings_common import router as common_router
from .bookings_manager import router as manager_router

router = APIRouter()

router.include_router(
    common_router
)  # booking routes common to dc_manager and dc_pool_manager
router.include_router(manager_router)  # booking routes specific to dc_manager only
