from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Integer, String, and_, bindparam, text
from sqlmodel import select

from api.v2.orm.json_varchar import JSONVarchar

if TYPE_CHECKING:
    from sqlalchemy.sql.selectable import TextualSelect
    from sqlmodel.sql.expression import SelectOfScalar


def query_referenced_canvas_id(
    dc_engagement_id: int, canvas_id: int, dc_user_id: int
) -> "SelectOfScalar[int]":
    """
    Create a query to return a dc_engagement_id and canvas_id for a user claiming to be associated with it.

    Imports are included in the function to avoid circular imports.

    """

    from api.v2.orm import V2CamEngagement, V2Canvas, V2Engagement

    query = (
        select(V2Canvas.canvas_id)
        .join(
            V2Engagement,
            and_(
                V2Canvas.dc_engagement_id == V2Engagement.dc_engagement_id,
                V2Engagement.is_deleted == "F",
                V2Engagement.dc_engagement_id == dc_engagement_id,
            ),
        )
        .join(
            V2CamEngagement,
            and_(
                V2Engagement.dc_engagement_id == V2CamEngagement.dc_engagement_id,
                V2CamEngagement.is_deleted == "F",
                V2CamEngagement.user_id == dc_user_id,
            ),
        )
        .where(V2Canvas.canvas_id == canvas_id)
    )
    return query


def query_canvas_external_runs(canvas_id: int) -> "TextualSelect":
    stmt = (
        text(
            """WITH
    scoped_cte AS (SELECT
                       PARSE_JSON( workflow_data ) AS workflow_data,
                       create_dtm
                       FROM
                           dc_wf_background_job
                       WHERE dc_wf_background_job.canvas_id = :canvas_id
                         AND dc_wf_background_job.is_deleted = 'F'
                         AND dc_wf_background_job.workflow_data IS NOT NULL
                  )
SELECT
    CASE
        WHEN workflow_data:canvas_type = 'unified view canvas'
            THEN
            OBJECT_CONSTRUCT_KEEP_NULL(
                    'canvas_id', :canvas_id,
                    'canvas_name', workflow_data:canvas_name,
                    'canvas_desc', workflow_data:canvas_desc,
                    'canvas_type', workflow_data:canvas_type,
                    'dc_engagement_id', workflow_data:dc_engagement_id,
                    'files', NVL( workflow_data:files, ARRAY_CONSTRUCT( ) ),
                    'tag_ids', workflow_data:tag_ids,
                    'current_snapshot_name', workflow_data:current_snapshot_name,
                    'historical_snapshot_name', workflow_data:historical_snapshot_name,
                    'customer_request_ids', NVL( workflow_data:customer_request_ids, ARRAY_CONSTRUCT( ) ),
                    'collector_request_ids', NVL( workflow_data:collector_request_ids, ARRAY_CONSTRUCT( ) ),
                    'create_dtm', create_dtm
            )
        WHEN workflow_data:canvas_type IN ('current view canvas', 'current')
            THEN
            OBJECT_CONSTRUCT_KEEP_NULL(
                    'canvas_id', workflow_data:canvas_id,
                    'canvas_name', workflow_data:canvas_name,
                    'canvas_desc', workflow_data:canvas_desc,
                    'canvas_type', 'current view canvas',
                    'dc_engagement_id', workflow_data:dc_engagement_id,
                    'source_data_date_filter', workflow_data:source_data_date_filter,
                    'files', NVL( workflow_data:files, ARRAY_CONSTRUCT( ) ),
                    'tag_ids', workflow_data:tag_ids,
                    'customer_files', NVL( workflow_data:customer_files, ARRAY_CONSTRUCT( ) ),
                    'collector_files', NVL( workflow_data:collector_files, ARRAY_CONSTRUCT( ) ),
                    'create_dtm', create_dtm
            )
        WHEN workflow_data:canvas_type = 'sourced file canvas'
            THEN
            OBJECT_CONSTRUCT_KEEP_NULL(
                    'canvas_id', workflow_data:canvas_id,
                    'canvas_name', workflow_data:canvas_name,
                    'canvas_desc', workflow_data:canvas_desc,
                    'canvas_type', workflow_data:canvas_type,
                    'dc_engagement_id', workflow_data:dc_engagement_id,
                    'files', NVL( workflow_data:files, ARRAY_CONSTRUCT( ) ),
                    'create_dtm', create_dtm
            )
        END AS canvas_parameters
    FROM
        scoped_cte;
    """
        )
        .bindparams(bindparam("canvas_id", canvas_id, type_=Integer))
        .columns(canvas_parameters=JSONVarchar)
    )

    return stmt


def query_engagement_canvases(dc_engagement_id: int, logged_user: str):
    stmt = (
        text(
            """
    with canvas as (
            select  h.CANVAS_ID,
                    h.DC_ENGAGEMENT_ID,
                    h.CANVAS_NAME,
                    h.CANVAS_STATUS,
                    NVL(h.CANVAS_TYPE, 'unified view canvas') AS CANVAS_TYPE,
                    NVL(h.CANVAS_DESC,'') AS CANVAS_DESC,
                    h.CREATE_DTM,
                    h.NOTIFICATION_ID,
                    h.current_snapshot_name,
                    h.historical_snapshot_name,
                    h.ENABLED
            from DC_CANVAS_HDR h
                join DC_CAM_TO_ENGAGEMENT c on ( c.DC_ENGAGEMENT_ID = h.DC_ENGAGEMENT_ID )
                join DC_USERS u on ( u.USER_ID = c.USER_ID )
            where h.DC_ENGAGEMENT_ID = :dc_engagement_id
                  and u.CISCO_CCO_ID = :logged_user
                  and h.IS_DELETED = 'F'
                  and c.IS_DELETED = 'F'
                  and u.IS_DELETED = 'F'
        ),tag_actions as (
            select t.CANVAS_ID,
                   sum(case when t.USER_ACTION = 'extract' then t.COUNT_INSTANCES   else 0 end) AS EXTRACT_ACTIONS,
                   sum(case when t.USER_ACTION in ('set','unset') then
                   t.COUNT_INSTANCES   else 0 end) AS TAG_ACTIONS
                    from DC_TAG_THOUGHTSPOT t
                    join canvas on (canvas.CANVAS_ID=t.CANVAS_ID)
                    where t.IS_DELETED ='F' and t.CREATED_BY = :logged_user
                    group by t.CANVAS_ID
        )
        select
                      OBJECT_CONSTRUCT(
                               'create_dtm'      , c.CREATE_DTM,
                               'canvas_id'       , c.CANVAS_ID,
                               'canvas_name'     , c.CANVAS_NAME,
                               'canvas_status'   , c.CANVAS_STATUS,
                               'canvas_type'     , c.CANVAS_TYPE,
                               'canvas_desc'     , c.CANVAS_DESC,
                               'dc_engagement_id', c.DC_ENGAGEMENT_ID,
                               'notification_id' , c.NOTIFICATION_ID,
                               'tag_actions'     , NVL(t.TAG_ACTIONS, 0),
                               'extract_actions' , NVL(t.EXTRACT_ACTIONS, 0),
                               'current_snapshot_name', c.CURRENT_SNAPSHOT_NAME,
                               'historical_snapshot_name', c.HISTORICAL_SNAPSHOT_NAME,
                               'enabled'         , c.ENABLED,
                               'pinboards'       , array_agg(
                                                  IFF(p.DISPLAY_NAME IS NOT NULL AND p.GUID IS NOT NULL,
                                                  --- Prevent empty objects from being added to the array
                                                  OBJECT_CONSTRUCT
                                               (
                                                   'pinboard_name', p.DISPLAY_NAME,
                                                   'guid', p.guid
                                                ),
                                                NULL)
                               )
                           ) as canvas_row
                       from canvas c
                       left join DC_FILE_MANAGEMENT_LIVEBOARDS p on (c.CANVAS_ID = p.CANVAS_ID AND P.IS_DELETED='F')
                       left join tag_actions t on (t.CANVAS_ID = c.CANVAS_ID)
                       group by
                       c.CANVAS_ID, c.DC_ENGAGEMENT_ID, c.CANVAS_NAME,
                       c.CANVAS_STATUS, c.CANVAS_TYPE, c.CANVAS_DESC, t.TAG_ACTIONS, t.EXTRACT_ACTIONS,c.CREATE_DTM,
                          c.NOTIFICATION_ID, c.CURRENT_SNAPSHOT_NAME, c.HISTORICAL_SNAPSHOT_NAME, c.ENABLED
                       order by c.CANVAS_ID DESC
                       """
        )
        .bindparams(
            bindparam("dc_engagement_id", dc_engagement_id, type_=Integer),
            bindparam("logged_user", logged_user, type_=String),
        )
        .columns(canvas_row=JSONVarchar)
    )

    return stmt


def query_canvas_last_run_date(canvas_id):
    stmt = (
        text(
            """
            SELECT
            MAX(run_date) as last_run_date
            FROM dc_canvas_create_run_log
            WHERE canvas_id = :canvas_id
            GROUP BY canvas_id
            """
        )
        .bindparams(canvas_id=canvas_id)
        .columns(last_run_date=DateTime)
    )
    return stmt


def query_available_snapshots() -> "TextualSelect":
    from api.v2.models.enums import DbSchema
    from api.v2.orm import V2SnapshotData

    stmt = (
        text(
            """
            SELECT
            name,
            snapshot_date,
            nvl(snapshot_version, 0) as snapshot_version
            FROM IDENTIFIER(:snapshot_table)
            WHERE snapshot_date IS NOT NULL
            AND snapshot_date >= DATEADD('day', -100, CURRENT_DATE)
            AND IS_DELETED = 'F'
            ORDER BY snapshot_date DESC
            """
        )
        .bindparams(snapshot_table=f"{DbSchema.prod}.{V2SnapshotData.__tablename__}")
        .columns(name=String, snapshot_date=DateTime, snapshot_version=Integer)
    )
    return stmt


def query_latest_snapshot() -> "TextualSelect":
    from api.v2.models.enums import DbSchema
    from api.v2.orm import V2SnapshotData

    stmt = (
        text(
            """
            SELECT
            name,
            snapshot_date,
            nvl(snapshot_version, 0) as snapshot_version
            FROM IDENTIFIER(:snapshot_table)
            WHERE snapshot_date IS NOT NULL
            AND IS_DELETED = 'F'
            ORDER BY snapshot_date DESC
            LIMIT 1
            """
        )
        .bindparams(snapshot_table=f"{DbSchema.prod}.{V2SnapshotData.__tablename__}")
        .columns(name=String, snapshot_date=DateTime, snapshot_version=Integer)
    )
    return stmt


__all__ = [
    "query_available_snapshots",
    "query_canvas_external_runs",
    "query_canvas_last_run_date",
    "query_engagement_canvases",
    "query_latest_snapshot",
    "query_referenced_canvas_id",
]
