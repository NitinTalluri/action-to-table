from fastapi import APIRouter

from .engagements import router as engagements_router
from .contracts import router as contracts_router
from .workflows import router as workflows_router
from .tags import router as tags_router
from .tagsets import router as tagsets_router
from .stakeholders import router as stakeholders_router
from .canvas import router as canvas_router
from .links import router as links_router
from .thought_spot import router as thought_spot_router
from .dc_types import router as dc_types_router
from .thought_spot_tag import router as thought_spot_tag_router
from .file_management import router as file_management_router
from .admin import router as admin_router
from .user_defined_types import router as user_defined_types_router
from .users import router as users_router
from .documentation import router as documentation_router
from .manager import router as manager_router
from .support import router as support_router
from .announcements import router as announcements_router
from .sdp import router as user_sdp_router
from .static import router as static_router

router = APIRouter()
router.include_router(engagements_router, prefix="/engagements", tags=["EngagementsV2"])
router.include_router(tags_router, prefix="/tags", tags=["TagsV2"])
router.include_router(contracts_router, prefix="/contracts", tags=["ContractsV2"])
router.include_router(tagsets_router, prefix="/tagsets", tags=["TagSetsV2"])
router.include_router(
    stakeholders_router, prefix="/stakeholders", tags=["StakeholdersV2"]
)
router.include_router(canvas_router, prefix="/canvas", tags=["CanvasV2"])
router.include_router(links_router, prefix="/links", tags=["LinksV2"])
router.include_router(
    thought_spot_router, prefix="/thought_spot", tags=["thoughtspotV2"]
)
router.include_router(
    thought_spot_tag_router, prefix="/thought_spot_tag", tags=["thoughtspotTagV2"]
)
router.include_router(dc_types_router, prefix="/dc_types", tags=["DCTypesV2"])
router.include_router(users_router, prefix="/users", tags=["UsersV2"])
router.include_router(
    user_defined_types_router, prefix="/udt", tags=["UserDefinedTypesV2"]
)
router.include_router(
    file_management_router, prefix="/file_management", tags=["FileManagementV2"]
)
router.include_router(admin_router, prefix="/admin", tags=["AdminV2"])
router.include_router(workflows_router, prefix="/workflows", tags=["WorkflowsV2"])
router.include_router(
    documentation_router, prefix="/documentation", tags=["DocumentationV2"]
)
router.include_router(manager_router, prefix="/manager", tags=["ManagerV2"])
router.include_router(support_router, prefix="/support", tags=["SupportV2"])
router.include_router(
    announcements_router, prefix="/announcements", tags=["AnnouncementsV2"]
)
router.include_router(user_sdp_router, prefix="/sdp", tags=["SDP"])
router.include_router(static_router, prefix="/static", tags=["StaticV2"])
