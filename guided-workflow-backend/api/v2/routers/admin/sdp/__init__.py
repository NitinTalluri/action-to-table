from .sdp import router as sdp_router
from .subtasks import router as subtasks_router
from .tasks import router as tasks_router
from .lifecycles import router as lifecycles_router
from .deliverables import router as deliverables_router

sdp_router.include_router(
    tasks_router, prefix="/tasks", tags=["AdminSDP", "AdminSDPTasks"]
)
sdp_router.include_router(
    subtasks_router, prefix="/subtasks", tags=["AdminSDP", "SubAdminSDPTasks"]
)
sdp_router.include_router(
    lifecycles_router, prefix="/lifecycles", tags=["AdminSDP", "AdminSDPLifecycles"]
)
sdp_router.include_router(
    deliverables_router,
    prefix="/deliverables",
    tags=["AdminSDP", "AdminSDPDeliverables"],
)
