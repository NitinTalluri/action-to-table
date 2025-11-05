from fastapi import APIRouter

from api.dependencies import GetSessionDep, GetUserDep
from api.v2.models import (
    UserSDPCompletionDeliverablePayload,
    UserSDPCompletionDeliverableResponse,
)
from api.v2.services import UserSdpService

router = APIRouter()


@router.put("")
def put_sdp_completion(
    db_user: GetUserDep,
    session: GetSessionDep,
    payload: UserSDPCompletionDeliverablePayload,
) -> UserSDPCompletionDeliverableResponse:
    """Submit a newly completed deliverable, or revert a deliverable to incomplete."""
    with UserSdpService(session=session) as service:
        service.process_completion(payload=payload, requestor=db_user)
        session.commit()
        response = service.get_completion(
            sub_task_id=payload.sub_task_id,
            booking_contract=payload.booking_contract,
            dc_user_id=db_user.user_id,
            cycle_iterator=payload.cycle_iterator,
            dc_engagement_id=payload.dc_engagement_id,
            due_date=payload.due_date,
        )

    return response
