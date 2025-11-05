import logging

from fastapi import APIRouter

from api.dependencies import GetSessionDep
from api.v2.models import AdminSDPQueryAllResponse
from api.v2.queries.admin.sdp import query_admin_all_sdp, run_rebuild_sdp

router = APIRouter()
logger = logging.getLogger("api")


@router.get("", response_model=list[AdminSDPQueryAllResponse], tags=["AdminSDP"])
def get_sdp(session: GetSessionDep):
    """Get a high level view of all SDP Objects"""

    return session.exec(query_admin_all_sdp()).all()


@router.post("/rebuild", tags=["AdminSDP"])
def rebuild_sdp(session: GetSessionDep):
    """Manually recreate the Active, Scheduled, and Completed SDP items for users"""
    result = run_rebuild_sdp(session=session)
    return {"status": "success", "message": result}
