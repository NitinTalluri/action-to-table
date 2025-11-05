from typing import TYPE_CHECKING, Optional

from sqlalchemy import or_
from sqlmodel import select

if TYPE_CHECKING:
    from api.v2.models import V2SupportStatus


def query_agent_cases(
    statuses: Optional[list["V2SupportStatus"]] = None,
    assigned_cisco_cco_id: Optional[str] = None,
    assigned_user_id: Optional[int] = None,
    user_id: Optional[int] = None,
    user_cisco_cco_id: Optional[str] = None,
    case_id: Optional[int] = None,
):
    """
    Query support cases for agents with optional filters.
    """
    from api.v2.orm import SupportCase, V2User
    from api.v2.queries import query_user_org

    base_query = select(SupportCase).where(SupportCase.is_deleted == "F")

    if case_id is not None:
        base_query = base_query.where(SupportCase.case_id == case_id)

    if statuses:
        base_query = base_query.where(
            or_(*[SupportCase.status == status.value for status in statuses])
        )

    if assigned_cisco_cco_id:
        user_id_sq = (
            select(V2User.user_id)
            .where(V2User.cisco_cco_id == assigned_cisco_cco_id)
            .where(V2User.is_deleted == "F")
            .subquery()
        )
        base_query = base_query.where(SupportCase.agent_id == user_id_sq.c.user_id)

    if user_cisco_cco_id:
        user_id_sq = (
            select(V2User.user_id)
            .where(V2User.cisco_cco_id == user_cisco_cco_id)
            .where(V2User.is_deleted == "F")
            .subquery()
        )
        base_query = base_query.where(SupportCase.user_id == user_id_sq.c.user_id)

    if user_id:
        base_query = base_query.where(SupportCase.user_id == user_id)

    if assigned_user_id:
        base_query = base_query.where(SupportCase.agent_id == assigned_user_id)

    user_to_theater = query_user_org().cte()

    base_query = base_query.subquery()

    # noinspection PyArgumentList
    query = (
        select(
            *base_query.c,
            user_to_theater.c.dc_theater.label("dc_theater"),
        )
        .select_from(base_query)
        .join(
            user_to_theater,
            base_query.c.user_id == user_to_theater.c.user_id,
            isouter=True,
        )
    )

    return query


__all__ = ["query_agent_cases"]
