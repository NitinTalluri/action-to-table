from typing import Optional

from fastapi import APIRouter

from api.dependencies import GetSessionDep, UserRequest
from api.v2.models import (
    V2BookedContractsEntry,
    V2BookedContractsResponse,
    V2BookedContractsStoredProcParams,
)
from api.v2.queries import run_stored_procedure
from api.v2.queries.utils import GET_logged_user

router = APIRouter()


@router.post("", response_model=V2BookedContractsResponse)
def create_contract_entries(
    data: list[V2BookedContractsEntry],
    req: UserRequest,
    session: GetSessionDep,
    logged_user: Optional[str] = None,
):
    """
    Create contract entries
    """
    logged_user = GET_logged_user(req, logged_user)
    params = V2BookedContractsStoredProcParams(__root__=data)
    run_stored_procedure(
        params=params,
        session=session,
        proc_name="import_bookings",
        logged_user=logged_user,
    )
    return V2BookedContractsResponse(count=len(data))
