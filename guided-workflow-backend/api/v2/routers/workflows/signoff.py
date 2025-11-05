import logging
from typing import Union

from fastapi import APIRouter, HTTPException
from starlette.status import HTTP_401_UNAUTHORIZED

from api.dependencies import GetSessionDep, GetUserDep
from api.v2.models import V2DeferredSignOffAPI, V2SignedOffAPI, V2SignOffAPIResponse
from api.v2.orm import V2WfSignoff
from api.v2.queries import query_referenced_engagement_id

router = APIRouter()

logger = logging.getLogger("api")


@router.post("", response_model=V2SignOffAPIResponse, status_code=201)
def submit_sign_off(
    data: Union[V2SignedOffAPI, V2DeferredSignOffAPI],
    session: GetSessionDep,
    db_user: GetUserDep,
):
    """
    Submit a sign off or deferred sign off
    """

    # Ensure engagement exists
    query_engagement_id = query_referenced_engagement_id(
        data.dc_engagement_id, db_user.user_id
    )
    matched_engagement = session.exec(query_engagement_id).one()
    if not matched_engagement:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="User is not authorized to sign off this engagement",
        )

    # Create sign off
    db_signoff = V2WfSignoff.create_from_model(data, db_user.cisco_cco_id, session)

    return db_signoff
