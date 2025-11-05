from fastapi import APIRouter, Depends

from api.dependencies import is_support
from .user import router as user_cases_router
from .agent import router as agent_router

router = APIRouter()
router.include_router(user_cases_router, prefix="/cases")
router.include_router(agent_router, prefix="/agent", dependencies=[Depends(is_support)])
