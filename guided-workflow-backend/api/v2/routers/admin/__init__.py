from fastapi import APIRouter, Depends

from api.dependencies import require_admin, require_financial_admin
from .financial import router as financial_router
from .sdp import sdp_router

router = APIRouter()
router.include_router(
    financial_router,
    prefix="/financial",
    dependencies=[Depends(require_financial_admin)],
)
router.include_router(
    sdp_router,
    prefix="/sdp",
    tags=["ServiceDeliveryPlanV2"],
    dependencies=[Depends(require_admin)],
)
