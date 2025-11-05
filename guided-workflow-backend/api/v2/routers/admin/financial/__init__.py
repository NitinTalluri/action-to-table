from fastapi import APIRouter

router = APIRouter()

from .unverified import router as unverified_bookings_router  # noqa
from .verified import router as verified_bookings_router  # noqa
from .revenue import router as revenue_router  # noqa
from .contracts import router as contracts_router  # noqa

router.include_router(unverified_bookings_router, prefix="/bookings/unverified")
router.include_router(verified_bookings_router, prefix="/bookings/verified")
router.include_router(revenue_router, prefix="/revenue")
router.include_router(contracts_router, prefix="/contracts")
