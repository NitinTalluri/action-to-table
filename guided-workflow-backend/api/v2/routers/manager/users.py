from typing import Annotated, Optional

from fastapi import APIRouter, Query

from api.dependencies import GetSessionDep, GetUserDep
from api.v2.models.manager import V2ManagerUser
from api.v2.queries.manager.direct_reports import query_manager_users

router = APIRouter()

QueryScope = Query(
    ...,
    pattern="^(all|direct)$",
    title="Scope",
    description="Whether to return all users or only direct reports of the logged manager",
    example="direct",
)


@router.get("", response_model=list[V2ManagerUser])
def get_manager_users(
    session: GetSessionDep,
    db_user: GetUserDep,
    scope: Annotated[str, QueryScope] = "all",
    theater: Optional[str] = None,
):
    """
    Query either all users or only direct reports of the logged manager. The returned objects are extended with a
    field indicating whether the user is a direct report, in addition to total utilization and allocation data.
    """

    query = query_manager_users(
        db_user.cisco_cco_id, query_all=scope == "all", theater=theater
    )

    db_users = session.exec(query).all()
    return db_users
