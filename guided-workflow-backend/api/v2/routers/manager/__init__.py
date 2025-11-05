from fastapi import APIRouter, Depends

from api.dependencies import is_manager, is_pool_manager, is_manager_or_pool_manager
from .users import router as users_router
from .bookings import router as bookings_router
from .assignments import router as assignments_router
from .sdp import router as sdp_router
from .super_customers import router as super_customers_router
from .pool_manager import router as pool_manager_router

router = APIRouter()

# Routes accessible by manager or pool manager
router.include_router(
    users_router, prefix="/users", dependencies=[Depends(is_manager_or_pool_manager)]
)
router.include_router(
    bookings_router, prefix="/bookings"
)  # dependencies are handled in the booking modules

# Routes accessible by manager only
router.include_router(
    assignments_router,
    prefix="/bookings/assignments",
    dependencies=[Depends(is_manager)],
)
router.include_router(
    super_customers_router, prefix="/scv", dependencies=[Depends(is_manager)]
)

# Routes accessible by pool manager only
router.include_router(
    sdp_router, prefix="/bookings/sdp", dependencies=[Depends(is_pool_manager)]
)
router.include_router(
    pool_manager_router, prefix="/pool_manager", dependencies=[Depends(is_pool_manager)]
)
