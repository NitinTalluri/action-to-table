import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Integer, String, text

from api.v2.orm import JSONVarchar

if TYPE_CHECKING:
    from sqlalchemy.sql.selectable import TextualSelect


def query_notification_by_id(
    dc_engagement_id: int,
    notification_id: int,
) -> "TextualSelect":
    """
    Create a query to return a notification matching the provided notification_id and dc_engagement_id.

    The requesting User must either be the creator of the notification or have access to the engagement
    """
    stmt = (
        text(
            """WITH
    SCOPED_NOTIFICATIONS AS (SELECT
                                 NOTIFICATION_ID,
                                 ACTIONS.TREE_ID AS TREE_ID,
                                 N.NOTIFICATION_CATEGORY AS NOTIFICATION_CATEGORY,
                                 SUBJECT,
                                 N.DC_USER_ID,
                                 DC_ENGAGEMENT_ID,
                                 REQUEST_ID,
                                 ACTIONS.UI_ENUM AS WORKFLOW_ENUM,
                                 TRY_PARSE_JSON( DATA ) AS DATA,
                                 N.CREATE_DTM,
                                 N.UPDATE_DTM,
                                 N.CREATED_BY,
                                 NVL( N.UPDATE_DTM, N.CREATE_DTM ) AS LAST_UPDATED
                                 FROM
                                     DC_WF_NOTIFICATION N
                                         JOIN DC_WF_ACTION_ITEM ACTIONS ON ACTIONS.TREE_ID = N.TREE_ID
                                 WHERE
                                       DC_ENGAGEMENT_ID = :dc_engagement_id
                                   AND NOTIFICATION_ID = :notification_id
                                   
                            )
SELECT
    SN.NOTIFICATION_ID,
    SN.TREE_ID,
    SN.NOTIFICATION_CATEGORY,
    SN.SUBJECT,
    SN.DC_USER_ID,
    SN.DC_ENGAGEMENT_ID,
    SN.REQUEST_ID,
    SN.WORKFLOW_ENUM,
    BG.CANVAS_ID,
    NVL(SN.DATA, ARRAY_CONSTRUCT()) AS DATA,
    SN.CREATE_DTM,
    SN.UPDATE_DTM,
    SN.CREATED_BY,
    BG.EXTERNAL_JOB_ID AS EXTERNAL_JOB_ID,
    BG.EXTERNAL_RUN_ID AS EXTERNAL_RUN_ID
    FROM
        SCOPED_NOTIFICATIONS SN
            LEFT JOIN DC_WF_BACKGROUND_JOB BG ON BG.REQUEST_ID = SN.REQUEST_ID
    
    ORDER BY
        LAST_UPDATED
            
            
            
            """
        )
        .bindparams(
            dc_engagement_id=dc_engagement_id,
            notification_id=notification_id,
        )
        .columns(
            notification_id=Integer,
            tree_id=Integer,
            notification_category=String,
            subject=String,
            dc_user_id=Integer,
            dc_engagement_id=Integer,
            request_id=Integer,
            workflow_enum=String,
            data=JSONVarchar,
            create_dtm=DateTime,
            update_dtm=DateTime,
            created_by=String,
            external_job_id=String,
            external_run_id=String,
        )
    )

    return stmt


def query_engagement_notifications(
    dc_engagement_id: int,
    last_activity: Optional[datetime.datetime] = None,
) -> "TextualSelect":
    """
    Create a query to return notifications for an engagement. Additional filters can be applied to the query.
    last_activity should be converted to use the db_timezone before being passed to this function.

    If last_activity is not provided, the filter will remain but will use a date of 1970-01-01 00:00:00 UTC
    """

    activity_filter = (
        last_activity
        if last_activity is not None
        else datetime.datetime(1970, 1, 1, 0, 0, 0)
    )

    stmt = (
        text(
            """WITH
    SCOPED_NOTIFICATIONS AS (SELECT
                                 NOTIFICATION_ID,
                                 ACTIONS.TREE_ID AS TREE_ID,
                                 N.NOTIFICATION_CATEGORY AS NOTIFICATION_CATEGORY,
                                 SUBJECT,
                                 N.DC_USER_ID,
                                 DC_ENGAGEMENT_ID,
                                 REQUEST_ID,
                                 ACTIONS.UI_ENUM AS WORKFLOW_ENUM,
                                 TRY_PARSE_JSON( DATA ) AS DATA,
                                 N.CREATE_DTM,
                                 N.UPDATE_DTM,
                                 N.CREATED_BY,
                                 NVL( N.UPDATE_DTM, N.CREATE_DTM ) AS LAST_UPDATED
                                 FROM
                                     DC_WF_NOTIFICATION N
                                         JOIN DC_WF_ACTION_ITEM ACTIONS ON ACTIONS.TREE_ID = N.TREE_ID
                                 WHERE
                                       DC_ENGAGEMENT_ID = :dc_engagement_id
                                   AND LAST_UPDATED >= :last_activity
                            )
SELECT
    SN.NOTIFICATION_ID,
    SN.TREE_ID,
    SN.NOTIFICATION_CATEGORY,
    SN.SUBJECT,
    SN.DC_USER_ID,
    SN.DC_ENGAGEMENT_ID,
    SN.REQUEST_ID,
    SN.WORKFLOW_ENUM,
    BG.CANVAS_ID,
    SN.CREATE_DTM,
    SN.UPDATE_DTM,
    SN.CREATED_BY,
    BG.EXTERNAL_JOB_ID AS EXTERNAL_JOB_ID,
    BG.EXTERNAL_RUN_ID AS EXTERNAL_RUN_ID
    FROM
        SCOPED_NOTIFICATIONS SN
            LEFT JOIN DC_WF_BACKGROUND_JOB BG ON BG.REQUEST_ID = SN.REQUEST_ID
    WHERE
        SN.DATA IS NOT NULL
    ORDER BY
        LAST_UPDATED



    """
        )
        .bindparams(
            dc_engagement_id=dc_engagement_id,
            last_activity=activity_filter,
        )
        .columns(
            notification_id=Integer,
            tree_id=Integer,
            notification_category=String,
            subject=String,
            dc_user_id=Integer,
            dc_engagement_id=Integer,
            request_id=Integer,
            workflow_enum=String,
            create_dtm=DateTime,
            update_dtm=DateTime,
            created_by=String,
            external_job_id=String,
            external_run_id=String,
        )
    )

    return stmt


def query_users_notifications(
    dc_user_id: int,
    last_activity: Optional[datetime.datetime] = None,
):
    """
    Create a query to return notifications for a user.

    last_activity should be converted to use the db_timezone before being passed to this function.

    Parameters
    ----------
    cisco_cco_id : str
        User's cisco cco id
    dc_engagement_id : int
    last_activity : Optional[datetime]
    notification_id : Optional[int]

    """

    activity_filter = (
        last_activity
        if last_activity is not None
        else datetime.datetime(1970, 1, 1, 0, 0, 0)
    )

    stmt = (
        text(
            """WITH
    USER_ENGAGEMENTS     AS (SELECT
                                 DC_ENGAGEMENT_ID,
                                 USER_ID AS DC_USER_ID
                                 FROM
                                     DC_CAM_TO_ENGAGEMENT
                                 WHERE
                                       USER_ID = :dc_user_id
                                   AND IS_DELETED = 'F'
                            ),
    SCOPED_NOTIFICATIONS AS (SELECT
                                 NOTIFICATION_ID,
                                 ACTIONS.TREE_ID AS TREE_ID,
                                 N.NOTIFICATION_CATEGORY AS NOTIFICATION_CATEGORY,
                                 SUBJECT,
                                 N.DC_USER_ID,
                                 UE.DC_ENGAGEMENT_ID,
                                 REQUEST_ID,
                                 ACTIONS.UI_ENUM AS WORKFLOW_ENUM,
                                 TRY_PARSE_JSON( DATA ) AS DATA,
                                 N.CREATE_DTM,
                                 N.UPDATE_DTM,
                                 N.CREATED_BY,
                                 NVL( N.UPDATE_DTM, N.CREATE_DTM ) AS LAST_UPDATED
                                 FROM
                                     DC_WF_NOTIFICATION N
                                         JOIN USER_ENGAGEMENTS UE ON UE.DC_ENGAGEMENT_ID = N.DC_ENGAGEMENT_ID
                                         JOIN DC_WF_ACTION_ITEM ACTIONS ON ACTIONS.TREE_ID = N.TREE_ID
                                 WHERE
                                     LAST_UPDATED >= :last_activity
                            )
SELECT
    SN.NOTIFICATION_ID,
    SN.TREE_ID,
    SN.NOTIFICATION_CATEGORY,
    SN.SUBJECT,
    SN.DC_USER_ID,
    SN.DC_ENGAGEMENT_ID,
    SN.REQUEST_ID,
    SN.WORKFLOW_ENUM,
    BG.CANVAS_ID,
    SN.CREATE_DTM,
    SN.UPDATE_DTM,
    SN.CREATED_BY,
    BG.EXTERNAL_JOB_ID AS EXTERNAL_JOB_ID,
    BG.EXTERNAL_RUN_ID AS EXTERNAL_RUN_ID
    FROM
        SCOPED_NOTIFICATIONS SN
            LEFT JOIN DC_WF_BACKGROUND_JOB BG ON BG.REQUEST_ID = SN.REQUEST_ID
    WHERE
        SN.DATA IS NOT NULL
    ORDER BY
        LAST_UPDATED
            
            
            
            """
        )
        .bindparams(
            last_activity=activity_filter,
            dc_user_id=dc_user_id,
        )
        .columns(
            notification_id=Integer,
            tree_id=Integer,
            notification_category=String,
            subject=String,
            dc_user_id=Integer,
            dc_engagement_id=Integer,
            request_id=Integer,
            workflow_enum=String,
            create_dtm=DateTime,
            update_dtm=DateTime,
            created_by=String,
            external_job_id=String,
            external_run_id=String,
        )
    )

    return stmt
