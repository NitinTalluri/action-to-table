import logging

from sqlalchemy import Float, Integer, String, and_, distinct, func, text
from sqlmodel import Session, select

from api.v2.models import V2StoredProcedureResult
from api.v2.orm import JSONVarchar
from api.v2.orm.admin import (
    SDPTaskToDeliverable,
)
from api.v2.queries.stored_proc import (
    make_stored_proc_statement,
)

logger = logging.getLogger("api")


def query_admin_sdp_task(task_id: int):
    """
    Query the SDPTask attributes and construct an array of subtask_ids (if any) that it is linked to
    """
    query = (
        text(
            """
    SELECT DC_SDP_TYP_TASK.TASK_ID as task_id,
       NVL(DC_SDP_TYP_TASK.TASK_DESC, '') as task_desc,
        DC_SDP_TYP_TASK.TASK_DESC_LONG as task_desc_long,
       DC_SDP_TYP_TASK.TASK_DOC_LINK as task_doc_link,
       NVL(DC_SDP_TYP_TASK.HOURS, 0.0) as hours,
       NVL(DC_SDP_TYP_TASK.FREQUENCY, 0) as frequency,
       DC_SDP_TYP_TASK.ANCHOR_DATE_ID as anchor_date_id,
       DC_SDP_TYP_TASK.CYCLE_ITERATOR_ID as cycle_iterator_id,
       NVL(DC_SDP_TYP_TASK.DUE_DATE_OFFSET, 0) as due_date_offset,
       ARRAY_AGG(DISTINCT DC_SDP_TYP_DELIVERABLE.DELIVERABLE_ID)
                 WITHIN GROUP (ORDER BY DC_SDP_TYP_DELIVERABLE.DELIVERABLE_ID) AS DELIVERABLE_IDS,
       ARRAY_AGG(DISTINCT DC_SDP_TYP_SUBTASK.SUB_TASK_ID)
                 WITHIN GROUP (ORDER BY DC_SDP_TYP_SUBTASK.SUB_TASK_ID)        AS SUB_TASK_IDS
FROM DC_SDP_TYP_TASK
         LEFT OUTER JOIN DC_SDP_B_TASK_SUB_TASK ON DC_SDP_TYP_TASK.TASK_ID = DC_SDP_B_TASK_SUB_TASK.TASK_ID AND
                                                   DC_SDP_B_TASK_SUB_TASK.IS_DELETED = 'F'
         LEFT OUTER JOIN DC_SDP_TYP_SUBTASK
                         ON DC_SDP_B_TASK_SUB_TASK.SUB_TASK_ID = DC_SDP_TYP_SUBTASK.SUB_TASK_ID AND
                            DC_SDP_B_TASK_SUB_TASK.TASK_ID = :task_id AND
                            DC_SDP_TYP_SUBTASK.IS_DELETED = 'F'
         LEFT OUTER JOIN DC_SDP_B_TASK_TO_DELIVERABLE
                         ON DC_SDP_TYP_TASK.TASK_ID = DC_SDP_B_TASK_TO_DELIVERABLE.TASK_ID AND
                            DC_SDP_B_TASK_TO_DELIVERABLE.IS_DELETED = 'F'
         LEFT OUTER JOIN DC_SDP_TYP_DELIVERABLE
                         ON DC_SDP_B_TASK_TO_DELIVERABLE.DELIVERABLE_ID = DC_SDP_TYP_DELIVERABLE.DELIVERABLE_ID AND
                            DC_SDP_TYP_DELIVERABLE.IS_DELETED = 'F'
WHERE DC_SDP_TYP_TASK.IS_DELETED = 'F'
     AND DC_SDP_TYP_TASK.TASK_ID = :task_id
GROUP BY DC_SDP_TYP_TASK.TASK_ID, DC_SDP_TYP_TASK.TASK_DESC, DC_SDP_TYP_TASK.TASK_DOC_LINK, DC_SDP_TYP_TASK.HOURS,
         DC_SDP_TYP_TASK.FREQUENCY, DC_SDP_TYP_TASK.TASK_DESC_LONG, DC_SDP_TYP_TASK.ANCHOR_DATE_ID, DC_SDP_TYP_TASK.CYCLE_ITERATOR_ID,
            DC_SDP_TYP_TASK.DUE_DATE_OFFSET

    """
        )
        .bindparams(task_id=task_id)
        .columns(
            task_id=Integer,
            task_desc=String,
            task_desc_long=String,
            task_doc_link=String,
            anchor_date_id=Integer,
            cycle_iterator_id=Integer,
            due_date_offset=Integer,
            hours=Float,
            frequency=Integer,
            deliverable_ids=JSONVarchar,
            sub_task_ids=JSONVarchar,
        )
    )

    return query


def query_admin_sdp_tasks():
    """
    Query the SDPTask attributes and construct an array of subtask_ids (if any) that it is linked to
    """
    query = text(
        """
    SELECT DC_SDP_TYP_TASK.TASK_ID as task_id,
       NVL(DC_SDP_TYP_TASK.TASK_DESC, '') as task_desc,
       DC_SDP_TYP_TASK.TASK_DOC_LINK as task_doc_link,
       NVL(DC_SDP_TYP_TASK.HOURS, 0.0) as hours,
       NVL(DC_SDP_TYP_TASK.FREQUENCY, 0) as frequency,
       DC_SDP_TYP_TASK.ANCHOR_DATE_ID as anchor_date_id,
       DC_SDP_TYP_TASK.CYCLE_ITERATOR_ID as cycle_iterator_id,
       NVL(DC_SDP_TYP_TASK.DUE_DATE_OFFSET, 0) as due_date_offset,
       ARRAY_AGG(DISTINCT DC_SDP_TYP_DELIVERABLE.DELIVERABLE_ID)
                 WITHIN GROUP (ORDER BY DC_SDP_TYP_DELIVERABLE.DELIVERABLE_ID) AS DELIVERABLE_IDS,
       ARRAY_AGG(DISTINCT DC_SDP_TYP_SUBTASK.SUB_TASK_ID)
                 WITHIN GROUP (ORDER BY DC_SDP_TYP_SUBTASK.SUB_TASK_ID)        AS SUB_TASK_IDS
FROM DC_SDP_TYP_TASK
         LEFT OUTER JOIN DC_SDP_B_TASK_SUB_TASK ON DC_SDP_TYP_TASK.TASK_ID = DC_SDP_B_TASK_SUB_TASK.TASK_ID AND
                                                   DC_SDP_B_TASK_SUB_TASK.IS_DELETED = 'F'
         LEFT OUTER JOIN DC_SDP_TYP_SUBTASK
                         ON DC_SDP_B_TASK_SUB_TASK.SUB_TASK_ID = DC_SDP_TYP_SUBTASK.SUB_TASK_ID AND
                            DC_SDP_TYP_SUBTASK.IS_DELETED = 'F'
         LEFT OUTER JOIN DC_SDP_B_TASK_TO_DELIVERABLE
                         ON DC_SDP_TYP_TASK.TASK_ID = DC_SDP_B_TASK_TO_DELIVERABLE.TASK_ID AND
                            DC_SDP_B_TASK_TO_DELIVERABLE.IS_DELETED = 'F'
         LEFT OUTER JOIN DC_SDP_TYP_DELIVERABLE
                         ON DC_SDP_B_TASK_TO_DELIVERABLE.DELIVERABLE_ID = DC_SDP_TYP_DELIVERABLE.DELIVERABLE_ID AND
                            DC_SDP_TYP_DELIVERABLE.IS_DELETED = 'F'
WHERE DC_SDP_TYP_TASK.IS_DELETED = 'F'
GROUP BY DC_SDP_TYP_TASK.TASK_ID, DC_SDP_TYP_TASK.TASK_DESC, DC_SDP_TYP_TASK.TASK_DOC_LINK, DC_SDP_TYP_TASK.HOURS,
         DC_SDP_TYP_TASK.FREQUENCY, DC_SDP_TYP_TASK.ANCHOR_DATE_ID, DC_SDP_TYP_TASK.CYCLE_ITERATOR_ID, DC_SDP_TYP_TASK.DUE_DATE_OFFSET

    """
    ).columns(
        task_id=Integer,
        task_desc=String,
        task_doc_link=String,
        hours=Float,
        frequency=Integer,
        anchor_date_id=Integer,
        cycle_iterator_id=Integer,
        due_date_offset=Integer,
        deliverable_ids=JSONVarchar,
        sub_task_ids=JSONVarchar,
    )

    return query


def query_admin_sdp_subtask(sub_task_id: int):
    query = (
        text(
            """
            SELECT
            ST.SUB_TASK_ID,
            ST.SUBTASK_DESC,
            ST.SUBTASK_DESC_LONG,
            ST.SUBTASK_DOC_LINK,
            NVL(ST.HOURS, 0.0) AS HOURS,
            NVL(ST.FREQUENCY, 0) AS FREQUENCY,
            NVL(ST.CYCLE_DAYS, 0) AS CYCLE_DAYS,
            ARRAY_AGG( DISTINCT T.TASK_ID ) AS TASK_IDS,
            ARRAY_AGG( DISTINCT ST2EB.BUYING_PROGRAM_ID )
                       WITHIN GROUP (ORDER BY ST2EB.BUYING_PROGRAM_ID) AS BUYING_PROGRAM_TYPE_IDS,
            ARRAY_AGG( DISTINCT ST2EP.PRICING_MODEL_ID )
                       WITHIN GROUP (ORDER BY ST2EP.PRICING_MODEL_ID) AS PRICING_TYPE_IDS,
            ARRAY_AGG( DISTINCT ST2ES.SOLD_AS_SERVICE_ID )
                       WITHIN GROUP (ORDER BY ST2ES.SOLD_AS_SERVICE_ID) AS SOLD_AS_SERVICE_TYPE_IDS
            FROM
                DC_SDP_TYP_SUBTASK ST
                    LEFT OUTER JOIN DC_SDP_B_TASK_SUB_TASK T2S
                                    ON ST.SUB_TASK_ID = T2S.SUB_TASK_ID AND
                                       T2S.IS_DELETED = 'F'
                    LEFT OUTER JOIN DC_SDP_TYP_TASK T ON T2S.TASK_ID = T.TASK_ID AND
                                                       T.IS_DELETED = 'F'
                    LEFT OUTER JOIN DC_SDP_SUB_TASK_TO_ENAB_BUYING ST2EB
                                    ON ST.SUB_TASK_ID = ST2EB.SUB_TASK_ID AND
                                       ST2EB.IS_DELETED = 'F'
                    LEFT OUTER JOIN DC_SDP_SUB_TASK_TO_ENAB_PRICING ST2EP
                                    ON ST.SUB_TASK_ID = ST2EP.SUB_TASK_ID AND
                                       ST2EP.IS_DELETED = 'F'
                    LEFT OUTER JOIN DC_SDP_SUB_TASK_TO_ENAB_SOLD_AS ST2ES
                                    ON ST.SUB_TASK_ID = ST2ES.SUB_TASK_ID AND
                                       ST2ES.IS_DELETED = 'F'
            WHERE
                  ST.SUB_TASK_ID = :sub_task_id
              AND ST.IS_DELETED = 'F'
            GROUP BY
                ST.SUB_TASK_ID, ST.SUBTASK_DESC, ST.SUBTASK_DOC_LINK, ST.HOURS, ST.FREQUENCY, ST.SUBTASK_DESC_LONG, ST.CYCLE_DAYS
        
            """
        )
        .bindparams(sub_task_id=sub_task_id)
        .columns(
            sub_task_id=Integer,
            subtask_desc=String,
            subtask_desc_long=String,
            subtask_doc_link=String,
            hours=Float,
            frequency=Integer,
            cycle_days=Integer,
            task_ids=JSONVarchar,
            buying_program_type_ids=JSONVarchar,
            pricing_type_ids=JSONVarchar,
            sold_as_service_type_ids=JSONVarchar,
        )
    )
    return query


def query_admin_sdp_deliverable_detail(deliverable_id: int):
    from api.v2.orm.admin import SDPDeliverable

    query = (
        select(
            SDPDeliverable.deliverable_id,
            SDPDeliverable.deliverable_desc,
            SDPDeliverable.deliverable_doc_link,
            func.array_agg(distinct(SDPTaskToDeliverable.task_id))
            .within_group(SDPTaskToDeliverable.task_id)
            .label("task_ids"),
        )
        .select_from(SDPDeliverable)
        .join(
            SDPTaskToDeliverable,
            and_(
                SDPDeliverable.deliverable_id == SDPTaskToDeliverable.deliverable_id,
                SDPTaskToDeliverable.is_deleted == "F",
            ),
            isouter=True,
        )
        .where(SDPDeliverable.deliverable_id == deliverable_id)
        .where(SDPDeliverable.is_deleted == "F")
        .group_by(
            SDPDeliverable.deliverable_id,
            SDPDeliverable.deliverable_desc,
            SDPDeliverable.deliverable_doc_link,
        )
    )
    return query


def query_admin_sdp_lifecycles():
    from api.v2.orm.admin import SDPLifeCycle

    query = select(SDPLifeCycle).where(SDPLifeCycle.is_deleted == "F")
    return query


def query_admin_sdp_deliverables():
    from api.v2.orm.admin import SDPDeliverable

    query = select(SDPDeliverable).where(SDPDeliverable.is_deleted == "F")
    return query


def query_admin_all_sdp():
    """Make a query to get a view suitable for listing all SDP tasks, subtasks, and deliverables"""
    query = text(
        """
        SELECT
    DLVR.DELIVERABLE_DESC,
    DLVR.DELIVERABLE_ID,
    TASK.TASK_DESC,
    TASK.TASK_ID,
    TASK.ANCHOR_DATE_ID AS TASK_ANCHOR_DATE_ID,
    ANCHOR.ANCHOR_DATE_NAME AS TASK_ANCHOR_DATE_NAME,
    ITERATOR.ITERATOR_ID AS TASK_CYCLE_ITERATOR_ID,
    ITERATOR.ITERATOR_DATE_NAME AS TASK_CYCLE_ITERATOR_NAME,
    NVL(TASK.HOURS, 0.0) AS TASK_HOURS,
    NVL(TASK.FREQUENCY, 0) AS TASK_FREQUENCY,
    ST.SUBTASK_DESC,
    ST.SUB_TASK_ID,
    NVL(ST.HOURS, 0.0) AS SUBTASK_HOURS,
    NVL(ST.FREQUENCY, 0) AS SUBTASK_FREQUENCY,
    NVL(ST.CYCLE_DAYS, 0) AS SUBTASK_CYCLE_DAYS
    FROM
        DC_SDP_TYP_SUBTASK ST
            JOIN DC_SDP_B_TASK_SUB_TASK T2ST
                            ON ST.SUB_TASK_ID = T2ST.SUB_TASK_ID AND
                               T2ST.IS_DELETED = 'F'
            JOIN            DC_SDP_TYP_TASK TASK ON TASK.TASK_ID = T2ST.TASK_ID AND
                                               TASK.IS_DELETED = 'F'
            JOIN            DC_SDP_B_TASK_TO_DELIVERABLE T2D
                            ON TASK.TASK_ID = T2D.TASK_ID AND
                               T2D.IS_DELETED = 'F'
            JOIN            DC_SDP_TYP_DELIVERABLE DLVR
                            ON DLVR.DELIVERABLE_ID = T2D.DELIVERABLE_ID AND
                               DLVR.IS_DELETED = 'F'
            JOIN            DC_SDP_TYP_ANCHOR_DATE ANCHOR
                            ON ANCHOR.ANCHOR_DATE_ID = TASK.ANCHOR_DATE_ID AND
                               ANCHOR.IS_DELETED = 'F'
            JOIN            DC_SDP_TYP_ANCHOR_DATE_ITERATOR ITERATOR
                            ON ITERATOR.ITERATOR_ID = TASK.CYCLE_ITERATOR_ID AND
                               ITERATOR.IS_DELETED = 'F'
                               
                               """
    ).columns(
        deliverable_desc=String,
        deliverable_id=Integer,
        task_desc=String,
        task_id=Integer,
        task_hours=Float,
        task_frequency=Integer,
        task_anchor_date_id=Integer,
        task_anchor_date_name=String,
        task_cycle_iterator_id=Integer,
        task_cycle_iterator_name=String,
        subtask_desc=String,
        sub_task_id=Integer,
        subtask_hours=Float,
        subtask_frequency=Integer,
        subtask_cycle_days=Integer,
    )

    return query


def run_rebuild_sdp(session: "Session") -> V2StoredProcedureResult:
    from api.v2.services import ServiceException

    stmt = make_stored_proc_statement(has_params=False).bindparams(
        proc_name="dc_sdp_changes"
    )
    result = session.execute(stmt).scalar()
    parsed_result = V2StoredProcedureResult.parse_raw(result)
    if parsed_result.success:
        session.commit()
        return parsed_result
    raise ServiceException(msg=parsed_result.message, code=parsed_result.code)


__all__ = [
    "query_admin_all_sdp",
    "query_admin_sdp_deliverable_detail",
    "query_admin_sdp_deliverables",
    "query_admin_sdp_lifecycles",
    "query_admin_sdp_subtask",
    "query_admin_sdp_task",
    "query_admin_sdp_tasks",
    "run_rebuild_sdp",
]
