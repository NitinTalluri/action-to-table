from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Integer, String, func, text
from sqlmodel import select

from api.v2.orm import JSONVarchar

if TYPE_CHECKING:
    from sqlalchemy import Column
    from sqlalchemy.sql.selectable import TextualSelect
    from sqlmodel.sql.expression import SelectOfScalar

    from api.v2.orm import V2User


def _query_user_audiences(cisco_cco_id: str) -> "TextualSelect":
    """Given a user's cisco_cco_id, walk up heirarchy"""
    query = (
        text(
            """WITH
            mgr AS (SELECT TRY_TO_NUMBER( x.value ) AS manager_key
                        FROM
                            CPS_DSCI_API.ORGANIZATIONAL_HIERARCHY h,
                            LATERAL SPLIT_TO_TABLE( h.HIERARCHY_STRING, '.' ) x
                        WHERE
                              h.EMP_EMAIL = :cisco_cco_id
                          AND manager_key IS NOT NULL
                   )
        SELECT ARRAY_AGG( EMP_EMAIL ) AS AUDIENCE
            FROM
                ORGANIZATIONAL_HIERARCHY h
                    JOIN mgr ON (mgr.manager_key = h.CISCO_WORKER_PARTY_KEY)

        """
        )
        .bindparams(cisco_cco_id=cisco_cco_id)
        .columns(audience=JSONVarchar)
    )

    return query


def _query_user_announcement_ids(cisco_cco_id: str) -> "SelectOfScalar[Column]":
    """
    Retrieve a column of announcement ids that are not deleted and overlap with user's audience
    """
    base_announcements = text(
        """
        SELECT ID AS ANNOUNCEMENT_ID,
             PARSE_JSON(audience) AS audience
        FROM DC_ANNOUNCEMENTS
        where IS_DELETED = 'F'
        AND EXPIRATION_DATE > CURRENT_TIMESTAMP
        """
    ).columns(
        announcement_id=Integer,
        audience=JSONVarchar,
    )
    ba = base_announcements.subquery("base")
    ua = _query_user_audiences(cisco_cco_id=cisco_cco_id).cte("user_audience")
    overlap_aud = (
        # noinspection PyArgumentList
        select(ba.c.announcement_id).join(
            ua,
            func.array_size(func.array_intersection(ua.c.audience, ba.c.audience)) > 0,
        )
    )
    return overlap_aud


def _query_user_dismissed_announcements(user_id: int) -> "TextualSelect":
    """Retrieve a column of ids that a user has dismissed'"""
    stmt = (
        text(
            """
        SELECT announcement_id
        from DC_USER_TO_ANNOUNCEMENT
        where IS_DELETED = 'F'
        and IS_DISMISSED = true
        and USER_ID = :user_id
        """
        )
        .bindparams(user_id=user_id)
        .columns(
            announcement_id=Integer,
        )
    )

    return stmt


def query_user_announcements(user_id: int, cisco_cco_id: str, limit: int):
    """
    Queries for announcements where
    - the user is eligible to see based on audience
    - the user has not dismissed
    - the announcement has not expired
    - the announcement is not deleted
    """

    # Start with a column of announcement ids that user is eligible to see

    # Query for user announcement IDs
    base_announcements = _query_user_announcement_ids(cisco_cco_id=cisco_cco_id).cte(
        "user_announcements"
    )
    dismissed_announcements = _query_user_dismissed_announcements(user_id=user_id).cte(
        "dismissed_announcements"
    )

    target_announcements = select(base_announcements.c.announcement_id).where(
        base_announcements.c.announcement_id.notin_(
            select(dismissed_announcements.c.announcement_id)
        )
    )

    query = (
        text(
            """
        WITH main as (SELECT
        announce.ID AS ID,
        TITLE,
        SUBTITLE,
        BODY,
        CATEGORY,
        PRIORITY,
        announce.CREATE_DTM as CREATE_DTM,
        PUSH_DATE,
        EXPIRATION_DATE,
        AUDIENCE,
        ARRAY_AGG(
            OBJECT_CONSTRUCT(
                'id', link.id,
                'name', link.name,
                'href', link.href
            )
        )
          AS LINKS,
        FALSE AS IS_DISMISSED_BY_USER
        FROM DC_ANNOUNCEMENTS announce
        LEFT JOIN DC_ANNOUNCEMENT_LINK link ON (announce.ID = link.ANNOUNCEMENT_ID AND link.IS_DELETED = 'F')
        WHERE announce.IS_DELETED = 'F'
        AND EXPIRATION_DATE > CURRENT_TIMESTAMP
        GROUP BY announce.ID, TITLE, SUBTITLE, BODY, CATEGORY, PRIORITY, announce.CREATE_DTM, PUSH_DATE, EXPIRATION_DATE, AUDIENCE
        ORDER BY PRIORITY, announce.CREATE_DTM DESC)
        
        SELECT ID,
        TITLE,
        SUBTITLE,
        BODY,
        CATEGORY,
        PRIORITY,
        CREATE_DTM,
        PUSH_DATE,
        EXPIRATION_DATE,
        AUDIENCE,
        IS_DISMISSED_BY_USER,
        FILTER(main.links, l -> l:id IS NOT NULL) AS LINKS,
        FROM main
        LIMIT :limit
        
        """
        )
        .bindparams(limit=limit)
        .columns(
            id=Integer,
            title=String,
            subtitle=String,
            body=String,
            category=String,
            priority=Integer,
            push_date=String,
            expiration_date=String,
            audience=JSONVarchar,
            is_dismissed_by_user=Boolean,
            links=JSONVarchar,
        )
    )

    return select(
        *query.c,
    ).where(query.c.id.in_(target_announcements))


def query_announcements(user_id: int) -> "TextualSelect":
    """
    Get all announcements that are not deleted
    """
    query = (
        text(
            """
        with main as (SELECT
        announce.ID AS ID,
        TITLE,
        SUBTITLE,
        BODY,
        CATEGORY,
        PRIORITY,
        announce.CREATE_DTM as CREATE_DTM,
        PUSH_DATE,
        EXPIRATION_DATE,
        AUDIENCE,
        ARRAY_AGG(
            OBJECT_CONSTRUCT(
                'id', link.id,
                'name', link.name,
                'href', link.href
            )
        ) AS LINKS,
        NVL(USR_ANNOUNCE.IS_DISMISSED, FALSE) AS IS_DISMISSED_BY_USER
        FROM DC_ANNOUNCEMENTS announce
        LEFT JOIN DC_ANNOUNCEMENT_LINK link ON (announce.ID = link.ANNOUNCEMENT_ID AND link.IS_DELETED = 'F')
        LEFT JOIN DC_USER_TO_ANNOUNCEMENT USR_ANNOUNCE ON (USR_ANNOUNCE.ANNOUNCEMENT_ID = announce.ID AND USR_ANNOUNCE.USER_ID = :user_id)
        WHERE announce.IS_DELETED = 'F'
        GROUP BY announce.ID, TITLE, SUBTITLE, BODY, CATEGORY, PRIORITY, announce.CREATE_DTM, PUSH_DATE, EXPIRATION_DATE, AUDIENCE, USR_ANNOUNCE.IS_DISMISSED
        ORDER BY PRIORITY, announce.CREATE_DTM DESC)
        SELECT ID,
        TITLE,
        SUBTITLE,
        BODY,
        CATEGORY,
        PRIORITY,
        CREATE_DTM,
        PUSH_DATE,
        EXPIRATION_DATE,
        AUDIENCE,
        IS_DISMISSED_BY_USER,
        FILTER(main.links, l -> l:id IS NOT NULL) AS LINKS,
        FROM main
        """
        )
        .columns(
            id=Integer,
            title=String,
            subtitle=String,
            body=String,
            category=String,
            priority=Integer,
            push_date=String,
            expiration_date=String,
            audience=JSONVarchar,
            is_dismissed_by_user=Boolean,
            links=JSONVarchar,
        )
        .bindparams(user_id=user_id)
    )

    return query


def query_announcement_by_id(announcement_id: int, user_id: int):
    query = (
        text(
            """
        WITH main as (
        SELECT
        announce.ID AS ID,
        TITLE,
        SUBTITLE,
        BODY,
        CATEGORY,
        PRIORITY,
        announce.CREATE_DTM AS CREATE_DTM,
        
        PUSH_DATE,
        EXPIRATION_DATE,
        AUDIENCE,
        ARRAY_AGG(
            OBJECT_CONSTRUCT(
                'id', link.id,
                'name', link.name,
                'href', link.href
            )
        ) AS LINKS,
        NVL(USR_ANNOUNCE.IS_DISMISSED, FALSE) AS IS_DISMISSED_BY_USER
        FROM DC_ANNOUNCEMENTS announce
        LEFT JOIN DC_ANNOUNCEMENT_LINK link ON (announce.ID = link.ANNOUNCEMENT_ID AND link.IS_DELETED = 'F')
        LEFT JOIN DC_USER_TO_ANNOUNCEMENT USR_ANNOUNCE ON (USR_ANNOUNCE.ANNOUNCEMENT_ID = announce.ID AND USR_ANNOUNCE.USER_ID = :user_id)
        WHERE announce.IS_DELETED = 'F'
        AND announce.id = :announcement_id
        GROUP BY announce.ID, TITLE, SUBTITLE, BODY, CATEGORY, PRIORITY, announce.CREATE_DTM, PUSH_DATE, EXPIRATION_DATE, AUDIENCE, USR_ANNOUNCE.IS_DISMISSED
        ORDER BY PRIORITY, announce.CREATE_DTM DESC
        )
        SELECT ID,
        TITLE,
        SUBTITLE,
        BODY,
        CATEGORY,
        PRIORITY,
        CREATE_DTM,
        PUSH_DATE,
        EXPIRATION_DATE,
        AUDIENCE,
        IS_DISMISSED_BY_USER,
        FILTER(main.links, l -> l:id IS NOT NULL) AS LINKS,
        FROM main
        LIMIT 1
        """
        )
        .bindparams(announcement_id=announcement_id, user_id=user_id)
        .columns(
            id=Integer,
            title=String,
            subtitle=String,
            body=String,
            category=String,
            priority=Integer,
            push_date=String,
            expiration_date=String,
            audience=JSONVarchar,
            is_dismissed_by_user=Boolean,
            links=JSONVarchar,
        )
    )

    return query
