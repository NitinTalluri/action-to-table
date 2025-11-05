from typing import TYPE_CHECKING, NamedTuple, TypedDict

from sqlalchemy import Integer, String, text

from api.v2.orm import JSONVarchar

if TYPE_CHECKING:
    from sqlalchemy.sql.selectable import TextualSelect
    from sqlmodel import Session

    from api.v2.models import V2SuperCustomerResponse


def query_engagement_name_map() -> "TextualSelect":
    """
    Build a lightweight query that provides a mapping of engagement_id : engagement_name
    """
    stmt = text(
        """
    SELECT
    DC_ENGAGEMENT_ID::VARCHAR as DC_ENGAGEMENT_ID,
    NVL(ENGAGEMENT_NAME, '') as ENGAGEMENT_NAME
    FROM
        DC_ENGAGEMENT_HDR
    WHERE
        IS_DELETED = 'F'
    """
    ).columns(dc_engagement_id=String, engagement_name=String)
    return stmt


def query_super_customers():
    stmt = text(
        # language=Snowflake
        """
    SELECT
                             SC.SUPER_CUSTOMER_ID,
                             SC.SUPER_CUSTOMER_NAME,
                             NVL( ARRAY_AGG( DISTINCT DC_ENGAGEMENT_ID ) WITHIN GROUP ( ORDER BY DC_ENGAGEMENT_ID ), ARRAY_CONSTRUCT( ) ) AS DC_ENGAGEMENT_IDS
                             FROM
                                 DC_SUPER_CUSTOMER SC
                                     LEFT JOIN DC_SUPER_CUSTOMER_ENGAGEMENTS SCE ON (
                                     SC.SUPER_CUSTOMER_ID = SCE.SUPER_CUSTOMER_ID
                                         AND SCE.IS_DELETED = 'F'
                                     )
                             WHERE
                                 SC.IS_DELETED = 'F'
                             GROUP BY
                                 SC.SUPER_CUSTOMER_ID,
                                 SC.SUPER_CUSTOMER_NAME
    """
    ).columns(
        super_customer_id=Integer,
        super_customer_name=String,
        dc_engagement_ids=JSONVarchar,
    )

    return stmt


def query_not_super_engagements() -> "TextualSelect":
    stmt = text(
        # language=Snowflake
        """
    SELECT
        DC_ENGAGEMENT_ID
    FROM
        DC_ENGAGEMENT_HDR
    WHERE
        IS_DELETED = 'F'
        AND DC_ENGAGEMENT_ID NOT IN (
            SELECT DISTINCT
                SCE.DC_ENGAGEMENT_ID
            FROM
                DC_SUPER_CUSTOMER_ENGAGEMENTS SCE
            WHERE
                SCE.IS_DELETED = 'F'
        )
    """
    ).columns(
        dc_engagement_id=Integer,
    )

    return stmt


class SuperCustomerQueryResult(NamedTuple):
    names: dict[str, str]
    super_customers: list
    available_engagements: list[int]


def get_super_customer_response(db_session: "Session") -> "SuperCustomerQueryResult":
    engagement_names_query = query_engagement_name_map()
    super_customers = query_super_customers()
    unlinked_engagements = query_not_super_engagements()

    engagement_names_result = {
        row["dc_engagement_id"]: row["engagement_name"]
        for row in db_session.execute(engagement_names_query).mappings().all()
    }
    super_customers_result = db_session.execute(super_customers).all()
    unlinked_engagements_result = (
        db_session.execute(unlinked_engagements).scalars().all()
    )

    return SuperCustomerQueryResult(
        names=engagement_names_result,
        super_customers=super_customers_result,
        available_engagements=unlinked_engagements_result,
    )
