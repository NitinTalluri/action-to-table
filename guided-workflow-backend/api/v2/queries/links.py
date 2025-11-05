from typing import TYPE_CHECKING

from sqlalchemy import Date, Integer, String, text
from toolz import groupby

from api.v2.models import V2EngagementLinks

if TYPE_CHECKING:
    from sqlalchemy.sql.selectable import TextualSelect
    from sqlmodel import Session


def query_engagement_links(dc_engagement_id: int) -> "TextualSelect":
    """
    Query all externally linked identifiers for a given engagement.

    Where implemented (ACAT and MCE), query the last updated date for the link
    """

    stmt = (
        text(
            """
       WITH ENGAGEMENT AS (
        SELECT DC_ENGAGEMENT_ID FROM DC_ENGAGEMENT_HDR WHERE DC_ENGAGEMENT_ID = :dc_engagement_id
        AND IS_DELETED = 'F'
        ),
        ACAT_LINKS AS (
            SELECT ACAT_CUSTOMER_ID AS ID, 'acat_links' AS LINK_TYPE
            FROM DC_ACAT_LINKS ACT
            JOIN ENGAGEMENT E ON ACT.DC_ENGAGEMENT_ID = E.DC_ENGAGEMENT_ID
            WHERE ACT.IS_DELETED = 'F'
        ),
        ACAT_LAST_UPDATED AS (
            SELECT AL.ID AS ID, AL.LINK_TYPE AS LINK_TYPE, MAX(D.LAST_UPDATE_DATE::DATE) AS LAST_UPDATED
            FROM ACAT_LINKS AL
            LEFT JOIN SERVICES_DB.SERVICES_IB_FBV.BV_IBSA_ACAT_DISCOVERY_SUM D ON (D.CUSTOMER_ID = AL.ID and D.TOTAL_LINES > 0
                AND D.REQUEST_TYPE IN ('ON-DEMAND', 'Discovery(System)')
                AND D.DATA_PURGED LIKE 'RETAIN%'
                )
            LEFT JOIN SERVICES_DB.SERVICES_IB_FBV.BV_IBSA_ACAT_CUSTOMER_MASTER M ON (M.CUSTOMER_ID = D.CUSTOMER_ID)
            GROUP BY AL.ID, AL.LINK_TYPE
        ),
        MCE_LINKS AS (
            SELECT MCE_ENGAGEMENT_NUMBER AS ID, 'mce_links' AS LINK_TYPE
            FROM DC_MCE_LINKS MCL
            JOIN ENGAGEMENT E ON MCL.DC_ENGAGEMENT_ID = E.DC_ENGAGEMENT_ID
            WHERE MCL.IS_DELETED = 'F'
        ),
        MCE_LAST_UPDATED AS (
            SELECT ML.ID AS ID, ML.LINK_TYPE AS LINK_TYPE, MAX(H.LAST_UPDATED_DATE::DATE) AS LAST_UPDATED
            FROM MCE_LINKS ML
            left JOIN SERVICES_DB.SERVICES_ENT_FBV.BV_MCE_AM_ENGAGEMENT_HDR H ON (H.ENGAGEMENT_NUMBER = ML.ID)
            GROUP BY ML.ID, ML.LINK_TYPE
        ),
        PARTY_LINKS AS (
            SELECT CR_PARTY_ID AS ID, 'party_links' AS LINK_TYPE, NULL AS LAST_UPDATED
            FROM DC_PARTY_LINKS PL
            JOIN ENGAGEMENT E ON PL.DC_ENGAGEMENT_ID = E.DC_ENGAGEMENT_ID
            WHERE PL.IS_DELETED = 'F'
        ),
        SMART_LINKS AS (
            SELECT SMART_ACCOUNT AS ID, 'smart_links' AS LINK_TYPE, NULL AS LAST_UPDATED
            FROM DC_SMART_ACCOUNT_LINKS SL
            JOIN ENGAGEMENT E ON SL.DC_ENGAGEMENT_ID = E.DC_ENGAGEMENT_ID
            WHERE SL.IS_DELETED = 'F'
        ),
        LINKS AS (
            SELECT ID, LINK_TYPE, nvl(LAST_UPDATED,'2000-01-01'::date) as LAST_UPDATED FROM ACAT_LAST_UPDATED
            UNION ALL
            SELECT ID, LINK_TYPE, nvl(LAST_UPDATED,'2000-01-01'::date) as LAST_UPDATED FROM MCE_LAST_UPDATED
            UNION ALL
            SELECT ID, LINK_TYPE, LAST_UPDATED FROM PARTY_LINKS
            UNION ALL
            SELECT ID, LINK_TYPE, LAST_UPDATED FROM SMART_LINKS
        )
        SELECT ID, :dc_engagement_id AS DC_ENGAGEMENT_ID, LINK_TYPE, LAST_UPDATED FROM LINKS
        """
        )
        .bindparams(dc_engagement_id=dc_engagement_id)
        .columns(
            id=Integer, dc_engagement_id=Integer, link_type=String, last_updated=Date
        )
    )

    return stmt


def get_engagement_links(
    dc_engagement_id: int, session: "Session"
) -> V2EngagementLinks:
    """Query and fetch the engagement links"""

    stmt = query_engagement_links(dc_engagement_id=dc_engagement_id)
    db_links = session.execute(stmt).mappings().all()

    if not db_links:
        return V2EngagementLinks()

    rows_by_type = groupby(lambda row: row["link_type"], db_links)

    return V2EngagementLinks(
        acat_links=rows_by_type.get("acat_links", []),
        mce_links=rows_by_type.get("mce_links", []),
        party_links=rows_by_type.get("party_links", []),
        smart_links=rows_by_type.get("smart_links", []),
    )


__all__ = ["get_engagement_links", "query_engagement_links"]
