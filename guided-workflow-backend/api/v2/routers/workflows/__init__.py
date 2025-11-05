from fastapi import APIRouter

from .signoff import router as sign_off_router
from .actions import router as actions_router
from .notifications import router as notifications_router
from .workflow_tagging import router as workflow_tagging_router
from .evidence_uploads import router as evidence_uploads_router
from .downloads import router as downloads_router
from .lookups import router as lookups_router
from .sea_upload import router as sea_upload_router
from .macd import router as macd_router

router = APIRouter()

router.include_router(sign_off_router, prefix="/sign_off", tags=["SignOffV2"])
router.include_router(actions_router, prefix="/actions", tags=["ActionsV2"])
router.include_router(
    notifications_router, prefix="/notifications", tags=["NotificationsV2"]
)
router.include_router(workflow_tagging_router)
router.include_router(
    evidence_uploads_router, prefix="/evidence_uploads", tags=["EvidenceUploadsV2"]
)
router.include_router(downloads_router, prefix="/downloads", tags=["DownloadsV2"])
router.include_router(lookups_router, prefix="/lookups", tags=["LookupsV2"])
router.include_router(sea_upload_router, tags=["SEAUploadsV2"])

router.include_router(macd_router, prefix="/macd", tags=["MACDV2"])
