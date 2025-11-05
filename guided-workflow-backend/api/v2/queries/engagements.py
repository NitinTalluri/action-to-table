from typing import TYPE_CHECKING

from sqlalchemy import and_
from sqlmodel import select

if TYPE_CHECKING:
    from sqlmodel.sql.expression import SelectOfScalar


def query_referenced_engagement_id(
    dc_engagement_id: int, dc_user_id: int
) -> "SelectOfScalar[int]":
    """
    Create a query to return a dc_engagement_id for a user claiming to be associated with it.

    Imports are included in the function to avoid circular imports.

    """

    from api.v2.orm import V2CamEngagement, V2Engagement

    query = (
        select(V2Engagement.dc_engagement_id)
        .join(
            V2CamEngagement,
            and_(
                V2Engagement.dc_engagement_id == V2CamEngagement.dc_engagement_id,
                V2CamEngagement.is_deleted == "F",
            ),
        )
        .where(V2CamEngagement.user_id == dc_user_id)
        .where(V2Engagement.dc_engagement_id == dc_engagement_id)
        .where(V2Engagement.is_deleted == "F")
    )
    return query


def query_users_engagements_by_user_id(user_id: int):
    """
    Create a query to return all engagements a user is associated with that are not deleted
    Parameters
    ----------
    user_id

    Returns
    -------

    """
    from api.v2.orm import V2CamEngagement, V2Engagement

    query = (
        select(V2Engagement)
        .where(V2Engagement.is_deleted == "F")
        .join(V2CamEngagement)
        .where(V2CamEngagement.is_deleted == "F")
        .where(V2CamEngagement.user_id == user_id)
    )
    return query
