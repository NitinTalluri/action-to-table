from operator import itemgetter

from fastapi import APIRouter
from toolz import groupby

from api.dependencies import GetSessionDep, GetUserDep
from api.v2.models import (
    UserSDPActiveDeliverableHeader,
    UserSDPClosedDeliverablesHeader,
    UserSDPEngagementDeliverable,
    safe_parse_collection,
)
from api.v2.models.sdp import UserSDPScheduledDeliverablesHeader
from api.v2.queries import (
    query_user_engagement_active_deliverables,
    query_user_engagement_closed_deliverables,
    query_user_engagement_deliverables,
    query_user_engagement_scheduled_deliverables,
)

router = APIRouter()


@router.get(
    "/{dc_engagement_id}/deliverables",
)
def get_user_engagement_deliverables(
    dc_engagement_id: int, session: GetSessionDep, db_user: GetUserDep
) -> list[UserSDPEngagementDeliverable]:
    """
    Query the deliverables for an engagement relevant to the user.

    *Referred to as 'View 1 (Summary)'*
    """

    query = query_user_engagement_deliverables(
        dc_engagement_id=dc_engagement_id, dc_user_id=db_user.user_id
    )
    results = session.exec(query).scalars().all()

    parsed = safe_parse_collection(list[UserSDPEngagementDeliverable], results)

    return parsed


@router.get(
    "/{dc_engagement_id}/deliverables/scheduled",
)
def get_user_engagement_scheduled_deliverables(
    dc_engagement_id: int, session: GetSessionDep, db_user: GetUserDep
) -> list[UserSDPScheduledDeliverablesHeader]:
    """
    Query the scheduled deliverables for an engagement relevant to the user keyed by 'header_name'

    *Referred to as 'View 2'*

    """

    query = query_user_engagement_scheduled_deliverables(
        dc_engagement_id=dc_engagement_id, dc_user_id=db_user.user_id
    )
    rows = session.exec(query).mappings().all()

    def make_response(db_rows: list[dict]):
        get_group_keys = itemgetter(
            "header_name",
            "booking_contract",
            "task_desc",
            "due_date",
            "cycle",
            "deliverable_id",
        )
        partitioned_rows: dict[str, dict] = groupby(get_group_keys, db_rows)
        for (
            header_name,
            booking_contract,
            task_desc,
            due_date,
            cycle,
            deliverable_id,
        ), rows in partitioned_rows.items():
            yield UserSDPScheduledDeliverablesHeader(
                header_name=header_name,
                booking_contract=booking_contract,
                task_desc=task_desc,
                due_date=due_date,
                cycle=cycle,
                tasks=rows,
                deliverable_id=deliverable_id,
            )

    return safe_parse_collection(
        list[UserSDPScheduledDeliverablesHeader], list(make_response(rows))
    )


@router.get(
    "/{dc_engagement_id}/deliverables/closed",
)
def get_user_engagement_closed_deliverables(
    dc_engagement_id: int, session: GetSessionDep, db_user: GetUserDep
) -> list[UserSDPClosedDeliverablesHeader]:
    """
    Query the scheduled deliverables for an engagement relevant to the user keyed by 'header_name'

    *Referred to as 'View 3'*
    """

    query = query_user_engagement_closed_deliverables(
        dc_engagement_id=dc_engagement_id, dc_user_id=db_user.user_id
    )

    rows = session.exec(query).mappings().all()

    def make_response(db_rows: list[dict]):
        get_group_keys = itemgetter(
            "header_name",
            "booking_contract",
            "task_desc",
            "due_date",
            "cycle",
            "deliverable_id",
        )
        partitioned_rows: dict[str, dict] = groupby(get_group_keys, db_rows)
        for (
            header_name,
            booking_contract,
            task_desc,
            due_date,
            cycle,
            deliverable_id,
        ), rows in partitioned_rows.items():
            yield UserSDPClosedDeliverablesHeader(
                header_name=header_name,
                booking_contract=booking_contract,
                task_desc=task_desc,
                due_date=due_date,
                cycle=cycle,
                tasks=rows,
                deliverable_id=deliverable_id,
            )

    return safe_parse_collection(
        list[UserSDPClosedDeliverablesHeader], list(make_response(rows))
    )


@router.get(
    "/{dc_engagement_id}/deliverables/active",
)
def get_user_engagement_active_deliverables(
    dc_engagement_id: int, session: GetSessionDep, db_user: GetUserDep
) -> list[UserSDPActiveDeliverableHeader]:
    """
    Query the scheduled deliverables for an engagement relevant to the user keyed by 'header_name'

    *Referred to as 'View 4'*
    """

    query = query_user_engagement_active_deliverables(
        dc_engagement_id=dc_engagement_id, dc_user_id=db_user.user_id
    )
    rows = session.exec(query).mappings().all()

    def make_response(db_rows: list[dict]):
        get_group_keys = itemgetter(
            "header_name",
            "booking_contract",
            "task_desc",
            "due_date",
            "cycle",
            "deliverable_id",
        )
        partitioned_rows: dict[str, dict] = groupby(get_group_keys, db_rows)
        for (
            header_name,
            booking_contract,
            task_desc,
            due_date,
            cycle,
            deliverable_id,
        ), rows in partitioned_rows.items():
            yield UserSDPActiveDeliverableHeader(
                header_name=header_name,
                booking_contract=booking_contract,
                task_desc=task_desc,
                due_date=due_date,
                cycle=cycle,
                deliverable_id=deliverable_id,
                tasks=rows,
            )

    return safe_parse_collection(
        list[UserSDPActiveDeliverableHeader], list(make_response(rows))
    )
