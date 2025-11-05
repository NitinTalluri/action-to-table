from typing import Optional

from sqlalchemy import and_, func, select, text, union


def query_manager_engagements(
    manager_email: str,
):
    """
    Query engagements for a given manager. This is a union between what they are explicitly associated with and what
    their direct reports are associated with.
    """

    from api.v2.orm import (
        V2CamEngagement,
        V2Engagement,
        V2User,
        v2_organizational_hierarchy,
    )

    # The actual emp_email column is subject to masking which will break our join so we make it ourselves
    emp_email = func.concat(v2_organizational_hierarchy.c.emp_cco_id, "@cisco.com")

    # Fixing the typo
    mgr_email = v2_organizational_hierarchy.c.mgr_emial.label("mgr_email")

    direct_report_user_ids = (
        select(
            V2User.user_id,
        )
        .join(
            v2_organizational_hierarchy,
            emp_email == V2User.cisco_cco_id,
        )
        .where(V2User.is_deleted == "F")
        .where(v2_organizational_hierarchy.c.emp_cco_id_masked.isnot(None))
        .where(mgr_email == manager_email)
        .distinct()
        .cte()
    )

    direct_report_engagements = (
        select(V2CamEngagement.dc_engagement_id)
        .where(V2CamEngagement.is_deleted == "F")
        .join(
            direct_report_user_ids,
            V2CamEngagement.user_id == direct_report_user_ids.c.user_id,
        )
        .join(
            and_(
                V2Engagement,
                V2Engagement.dc_engagement_id == V2CamEngagement.dc_engagement_id,
                V2Engagement.is_deleted == "F",
            )
        )
    )

    manager_engagements = (
        select(V2CamEngagement.dc_engagement_id)
        .where(V2CamEngagement.is_deleted == "F")
        .join(V2User, V2CamEngagement.user_id == V2User.user_id)
        .join(
            V2Engagement,
            and_(
                V2Engagement.dc_engagement_id == V2CamEngagement.dc_engagement_id,
                V2Engagement.is_deleted == "F",
            ),
        )
        .where(V2User.is_deleted == "F")
        .where(V2User.cisco_cco_id == manager_email)
    )

    engagement_ids = union(direct_report_engagements, manager_engagements)

    return engagement_ids


def query_manager_users(
    manager_email: str,
    query_all: bool,
    theater: Optional[str] = None,
    projected_days: int = 30,
):
    """
    Query users along with their allocation data for a given manager.

    If query_all is True, then all users are returned, otherwise only direct reports are returned.
    Also, if query_all is True, then the masked user display name is used, otherwise the actual user display name is

    Parameters:
        manager_email (str): The email of the manager to query users for.
        query_all (bool): If True, query all users, otherwise only direct reports.
        projected_days (int): The number of days to project utilization for.
    """

    from api.v2.orm import (
        V2SubAllocationReport,
        V2User,
        v2_organizational_hierarchy,
    )

    # First use a deduplicated CTE to to remove duplicate cisco_cco_id

    org_cte = (
        select(
            v2_organizational_hierarchy.c.emp_cco_id.label("emp_cco_id"),
            v2_organizational_hierarchy.c.emp_name,
        )
        .select_from(v2_organizational_hierarchy)
        .distinct()
        .cte()
    )

    # The actual emp_email column is subject to masking which will break our join so we make it ourselves
    emp_email_as_cisco_cco_id = func.concat(org_cte.c.emp_cco_id, "@cisco.com")

    # Fixing the typo
    mgr_email = v2_organizational_hierarchy.c.mgr_emial

    # Masked workers will have a display name that is like masked_XXX
    # If this is a query for all users, then we just use the masked name
    # If this is a query for direct reports, then we use the masked_XXX (cisco_cco_id) as the display name

    emp_display_name = func.concat(org_cte.c.emp_name, " (", org_cte.c.emp_cco_id, ")")

    heir_columns = [
        v2_organizational_hierarchy.c.level6_cisco_worker_name,
        v2_organizational_hierarchy.c.level7_cisco_worker_name,
        v2_organizational_hierarchy.c.level8_cisco_worker_name,
        emp_display_name.label("display_name"),
        org_cte.c.emp_cco_id.label("cisco_cco_id"),
        emp_email_as_cisco_cco_id.label("emp_email"),
        v2_organizational_hierarchy.c.dc_theater,
        mgr_email.label("mgr_email"),
    ]

    heir_base_cte = (
        select(*heir_columns)
        .select_from(org_cte)
        .join(
            v2_organizational_hierarchy,
            org_cte.c.emp_cco_id == v2_organizational_hierarchy.c.emp_cco_id,
        )
        .where(v2_organizational_hierarchy.c.emp_cco_id.isnot(None))
        .cte()
    )

    heir_cte = (
        select(
            heir_base_cte.c.level6_cisco_worker_name,
            heir_base_cte.c.level7_cisco_worker_name,
            heir_base_cte.c.level8_cisco_worker_name,
            heir_base_cte.c.display_name,
            heir_base_cte.c.dc_theater,
            heir_base_cte.c.mgr_email,
            heir_base_cte.c.emp_email,
            heir_base_cte.c.cisco_cco_id,
            V2User.user_id.label("user_id"),
            V2User.user_title.label("user_title"),
        )
        .select_from(V2User)
        .outerjoin(
            heir_base_cte,
            V2User.cisco_cco_id == heir_base_cte.c.emp_email,
        )
        .where(V2User.is_deleted == "F")
        .cte()
    )

    _total_gross_utilization = func.sum(
        V2SubAllocationReport.c.total_share_booking / 100
    ).label("total_gross_utilization")
    total_current_utilization = func.sum(
        func.iff(
            func.current_date().between(
                V2SubAllocationReport.c.agreement_start_date,
                V2SubAllocationReport.c.agreement_end_date,
            ),
            V2SubAllocationReport.c.total_share_booking / 100,
            0,
        )
    )

    tomorrow = func.dateadd(
        "day",
        1,
        func.current_date(),
    )
    projected_date = func.dateadd(
        "day",
        projected_days,
        func.current_date(),
    )

    projected_utilization = func.sum(
        func.iff(
            projected_date.between(
                V2SubAllocationReport.c.agreement_start_date,
                V2SubAllocationReport.c.agreement_end_date,
            ),
            V2SubAllocationReport.c.total_share_booking / 100,
            0,
        )
    ).label("projected_utilization")

    query_base = (
        select(
            func.nvl(heir_cte.c.display_name, heir_cte.c.cisco_cco_id).label(
                "display_name"
            ),
            heir_cte.c.user_id,
            heir_cte.c.user_title,
            V2User.cisco_cco_id,
            func.nvl(heir_cte.c.dc_theater, "UNKNOWN").label("theater"),
            total_current_utilization.label("total_utilization"),
            func.sum(
                func.iff(
                    V2SubAllocationReport.c.agreement_end_date.between(
                        tomorrow,
                        projected_date,
                    ),
                    V2SubAllocationReport.c.total_share_booking / 100,
                    0,
                )
            ).label("expiring_bookings"),
            func.sum(
                func.iff(
                    V2SubAllocationReport.c.agreement_start_date.between(
                        tomorrow,
                        projected_date,
                    ),
                    V2SubAllocationReport.c.total_share_booking / 100,
                    0,
                )
            ).label("starting_bookings"),
            projected_utilization.label("projected_utilization"),
            func.iff(
                heir_cte.c.mgr_email == manager_email,
                True,
                False,
            ).label("is_direct_report"),
        )
        .select_from(heir_cte)
        .outerjoin(
            V2SubAllocationReport,
            V2SubAllocationReport.c.emp_cco_id_masked == heir_cte.c.cisco_cco_id,
        )
        .join(V2User, heir_cte.c.emp_email == V2User.cisco_cco_id)
    )

    if not query_all:
        query_base = query_base.where(heir_cte.c.mgr_email == manager_email)

    if theater is not None:
        query_base = query_base.where(heir_cte.c.dc_theater == theater)

    query = query_base.group_by(
        heir_cte.c.display_name,
        heir_cte.c.mgr_email,
        heir_cte.c.dc_theater,
        heir_cte.c.cisco_cco_id,
        V2User.cisco_cco_id,
        heir_cte.c.user_id,
        heir_cte.c.user_title,
    ).order_by(
        text("is_direct_report desc, total_utilization"),
    )

    return query
