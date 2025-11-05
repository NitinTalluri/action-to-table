from typing import TYPE_CHECKING, Optional

from sqlalchemy import func
from sqlmodel import select

from api.v2.orm import V2CamEngagement, V2Engagement, V2User

if TYPE_CHECKING:
    from sqlmodel.sql.expression import SelectOfScalar

    from api.dependencies import UserRequest


def query_users_engagements(cisco_cco_id: str) -> "SelectOfScalar[V2Engagement]":
    """
    Given a username, return a SQLAlchemy Select object that will return all engagements for that user.
    This references the CAMEngagement model, which is the table that links users to engagements.

    Parameters
    ----------
    cisco_cco_id : str
        The username to get engagements for (User.cisco_cco_id)
    """

    query = (
        select(V2Engagement)
        .where(V2Engagement.is_deleted == "F")
        .join(V2CamEngagement)
        .where(V2CamEngagement.is_deleted == "F")
        .join(V2User)
        .where(V2User.is_deleted == "F")
        .where(V2User.cisco_cco_id == cisco_cco_id)
    )
    return query


def query_referenced_user(
    req: "UserRequest",
    logged_user: Optional[str] = None,
    dc_user_id: Optional[int] = None,
) -> "SelectOfScalar[V2User]":
    """
    Get the user that is referenced in the request. If logged_user is provided, it will be used to get the user.
    Otherwise, the user_id from the request will be used to get the user.
    """
    if not logged_user and not dc_user_id:
        raise ValueError("Either logged_user or user_id must be provided")

    from api.v2.orm import V2User
    from api.v2.queries.utils import GET_logged_user

    if logged_user:
        logged_user = GET_logged_user(req, logged_user)
        user_query = (
            select(V2User)
            .where(V2User.cisco_cco_id == logged_user)
            .where(V2User.is_deleted == "F")
        )
    else:
        user_query = (
            select(V2User)
            .where(V2User.user_id == dc_user_id)
            .where(V2User.is_deleted == "F")
        )

    return user_query


def query_available_users():
    from api.v2.orm import V2User, v2_organizational_hierarchy

    org_cte = (
        select(
            v2_organizational_hierarchy.c.emp_cco_id,
            v2_organizational_hierarchy.c.emp_name,
            v2_organizational_hierarchy.c.dc_theater,
        )
        .where(v2_organizational_hierarchy.c.emp_cco_id.isnot(None))
        .distinct()
        .cte()
    )

    user_names_cte = (
        select(
            func.concat(org_cte.c.emp_cco_id, "@cisco.com").label("cisco_cco_id"),
            org_cte.c.emp_name.label("display_name"),
            org_cte.c.dc_theater.label("dc_theater"),
        )
        .select_from(org_cte)
        .cte()
    )

    # noinspection PyArgumentList
    query = (
        select(
            V2User.cisco_cco_id,
            V2User.user_id,
            V2User.user_title,
            func.coalesce(user_names_cte.c.display_name, V2User.cisco_cco_id).label(
                "display_name"
            ),
            user_names_cte.c.dc_theater,
        )
        .where(V2User.is_deleted == "F")
        .where(V2User.cisco_cco_id.isnot(None))
        .where(V2User.user_id.isnot(None))
        .join(user_names_cte, V2User.cisco_cco_id == user_names_cte.c.cisco_cco_id)
    )

    return query


def query_user_org():
    """
    Construct a query suitable as a CTE of the form

    - user_id: The user's ID in DC
    - cisco_cco_id: The user's CCO ID (email)
    - display_name: The user's display name (from org hierarchy if available, otherwise CCO ID)
    - dc_theater: The user's theater (from org hierarchy if available, otherwise None)

    """
    from api.v2.orm import V2User, v2_organizational_hierarchy

    org_cte = (
        select(
            v2_organizational_hierarchy.c.emp_cco_id,
            v2_organizational_hierarchy.c.emp_name,
            v2_organizational_hierarchy.c.dc_theater,
        )
        .where(v2_organizational_hierarchy.c.emp_cco_id.isnot(None))
        .distinct()
        .cte()
    )

    user_names_cte = (
        select(
            func.concat(org_cte.c.emp_cco_id, "@cisco.com").label("cisco_cco_id"),
            org_cte.c.emp_name.label("display_name"),
            org_cte.c.dc_theater.label("dc_theater"),
        )
        .select_from(org_cte)
        .cte()
    )

    user_named_ids_cte = (
        select(
            V2User.user_id,
            V2User.cisco_cco_id,
            func.nvl(user_names_cte.c.display_name, V2User.cisco_cco_id).label(
                "display_name"
            ),
            user_names_cte.c.dc_theater,
        )
        .join(user_names_cte, V2User.cisco_cco_id == user_names_cte.c.cisco_cco_id)
        .where(V2User.is_deleted == "F")
    )

    return user_named_ids_cte
