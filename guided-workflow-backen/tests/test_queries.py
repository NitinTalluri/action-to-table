from sqlalchemy import select

from api.v2.orm import V2Engagement, V2CamEngagement, V2User


async def test_get_user_engagements(db_session, auth_username):
    from api.v2.queries.users import query_users_engagements

    q_engagements_query = (
        query_users_engagements(auth_username)
        .where(V2Engagement.is_deleted != "T")
        .where(V2CamEngagement.is_deleted != "T")
        .where(V2User.is_deleted != "T")
    )

    q_engagements = (
        db_session.execute(q_engagements_query).scalars().all()
    )

    # Manual query
    query = (
        select(V2Engagement)
        .where(V2Engagement.is_deleted == "F")
        .join(V2CamEngagement)
        .where(V2CamEngagement.is_deleted == "F")
        .join(V2User)
        .where(V2User.is_deleted == "F")
        .where(V2User.cisco_cco_id == auth_username)
    )
    db_engagements = db_session.execute(query).scalars().all()

    assert q_engagements == db_engagements
