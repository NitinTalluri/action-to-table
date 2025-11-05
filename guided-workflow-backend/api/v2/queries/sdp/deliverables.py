from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, Integer, String, text

from api.v2.orm import JSONVarchar

if TYPE_CHECKING:
    from sqlalchemy.sql import CompoundSelect
    from sqlalchemy.sql.selectable import TextualSelect


def query_user_engagement_deliverables(
    dc_engagement_id: int, dc_user_id: int
) -> "TextualSelect":
    """
    Query the deliverables for an engagement relevant to the user.

    Referred to as 'View 1 (Summary)'
    """
    query = (
        text(
            """SELECT DISTINCT OBJECT_CONSTRUCT_KEEP_NULL(
            'anchor_date', ANCHOR_DATE,
            'anchor_date_id', ANCHOR_DATE_ID,
            'booking_contract', DL.BOOKING_CONTRACT,
            'buying_program_name', SOLD_AS_BUYING_PROGRAM_NAME,
            'buying_program_type_id', BUYING_PROGRAM_TYPE_ID,
            'cycle_days', NVL( CYCLE_DAYS, 0 ),
            'dc_engagement_id', DL.DC_ENGAGEMENT_ID,
            'deliverable_desc', DELIVERABLE_DESC,
            'deliverable_id', DELIVERABLE_ID,
            'due_date_offset', NVL( DUE_DATE_OFFSET, 0 ),
            'engagement_name', ENGAGEMENT_NAME,
            'pricing_model_name', SOLD_AS_PRICING_MODEL_NAME,
            'pricing_model_type_id', SOLD_AS_PRICING_TYPE_ID,
            'sold_as_service_name', SOLD_AS_SERVICE_NAME,
            'sold_as_service_type_id', SOLD_AS_SERVICE_TYPE_ID,
            'sub_task_id', SUB_TASK_ID,
            'subtask_desc', SUBTASK_DESC,
            'task_desc', TASK_DESC,
            'time_cycle', NVL( ITERATOR_DATE_NAME, 'NOT SET' ),
            'task_id', TASK_ID
    ) AS deliverable
    FROM
        DC_DELIVERABLES_CORE_ENG DL
    JOIN DC_ENGAGEMENT_TO_BOOKINGS_RESPONSIBLE_USER ERU
            ON (DL.BOOKING_CONTRACT = ERU.BOOKING_CONTRACT AND DL.DC_ENGAGEMENT_ID = ERU.DC_ENGAGEMENT_ID AND ERU.IS_DELETED = 'F')
    JOIN DC_USERS USR ON (USR.USER_ID = ERU.DC_USER_ID AND USR.IS_DELETED = 'F')
    WHERE ERU.DC_ENGAGEMENT_ID = :dc_engagement_id
     AND ERU.DC_USER_ID = :dc_user_id
     AND USR.USER_ID = :dc_user_id
    """
        )
        .bindparams(dc_engagement_id=dc_engagement_id, dc_user_id=dc_user_id)
        .columns(deliverable=JSONVarchar)
    )

    return query


def query_user_engagement_scheduled_deliverables(
    dc_engagement_id: int, dc_user_id: int
) -> "TextualSelect":
    """
    Referred to as 'View 2 (Scheduled)'
    """
    query = (
        text(
            """
        SELECT DISTINCT
        DL.BOOKING_CONTRACT AS BOOKING_CONTRACT,
        DL.INDEX_POS AS CYCLE,
        USR.CISCO_CCO_ID AS CISCO_CCO_ID,
        DL.DC_ENGAGEMENT_ID AS DC_ENGAGEMENT_ID,
        DL.DELIVERABLE_DESC AS DELIVERABLE_DESC,
        DL.DELIVERABLE_ID AS DELIVERABLE_ID,
        DL.DUE_DATE AS DUE_DATE,
        DL.ENGAGEMENT_NAME AS ENGAGEMENT_NAME,
        DL.HEADER_NAME AS HEADER_NAME,
        DL.VISIBILITY_DATE AS SORT_DATE,
        DL.SUB_TASK_ID AS SUB_TASK_ID,
        DL.SUBTASK_DESC AS SUBTASK_DESC,
        DL.TASK_DESC AS TASK_DESC,
        DL.TASK_ID AS TASK_ID
        FROM DC_DELIVERABLES_OWED_SCHEDULED_ENG DL
        JOIN DC_ENGAGEMENT_TO_BOOKINGS_RESPONSIBLE_USER ERU
        ON (DL.BOOKING_CONTRACT = ERU.BOOKING_CONTRACT AND DL.DC_ENGAGEMENT_ID = ERU.DC_ENGAGEMENT_ID AND ERU.IS_DELETED = 'F')
        JOIN DC_USERS USR ON (USR.USER_ID = ERU.DC_USER_ID AND USR.IS_DELETED = 'F')
        WHERE ERU.DC_ENGAGEMENT_ID = :dc_engagement_id AND ERU.DC_USER_ID = :dc_user_id AND USR.USER_ID = :dc_user_id
        
    """
        )
        .bindparams(dc_engagement_id=dc_engagement_id, dc_user_id=dc_user_id)
        .columns(
            booking_contract=Integer,
            cycle=Integer,
            cisco_cco_id=String,
            dc_engagement_id=Integer,
            deliverable_desc=String,
            deliverable_id=Integer,
            due_date=String,
            engagement_name=String,
            header_name=String,
            sort_date=Date,
            sub_task_id=Integer,
            subtask_desc=String,
            task_desc=String,
            task_id=Integer,
        )
    )
    return query


def query_user_engagement_closed_deliverables(
    dc_engagement_id: int, dc_user_id: int
) -> "TextualSelect":
    """
    Referred to as 'View 3 (Closed)'
    """
    query = (
        text(
            """
    SELECT DISTINCT
    DL.BOOKING_CONTRACT AS BOOKING_CONTRACT,
    DL.COMPLETED_DATE::DATE AS CLOSED_DATE,
    DL.COMPLETED_CCO AS COMPLETED_BY,
    DL.COMPLETION_TYPE_ID AS COMPLETION_TYPE_ID,
    DL.INDEX_POS AS CYCLE,
    DL.DC_ENGAGEMENT_ID AS DC_ENGAGEMENT_ID,
    DL.DELIVERABLE_DESC AS DELIVERABLE_DESC,
    DL.DELIVERABLE_ID AS DELIVERABLE_ID,
    DL.DUE_DATE AS DUE_DATE,
    DL.HEADER_NAME AS HEADER_NAME,
    DL.ENGAGEMENT_NAME AS ENGAGEMENT_NAME,
    DL.COMPLETED_ST IS NOT NULL AS IS_CLOSED,
    DL.VISIBILITY_DATE AS SORT_DATE,
    DL.SUB_TASK_ID AS SUB_TASK_ID,
    DL.SUBTASK_DESC AS SUBTASK_DESC,
    DL.TASK_DESC AS TASK_DESC,
    DL.TASK_ID AS TASK_ID,
    DL.TASK_STATUS AS TASK_STATUS,
    USR.CISCO_CCO_ID AS CISCO_CCO_ID
    FROM DC_DELIVERABLES_CLOSED_VIEW_ENG DL
    JOIN DC_ENGAGEMENT_TO_BOOKINGS_RESPONSIBLE_USER ERU
    ON (DL.BOOKING_CONTRACT = ERU.BOOKING_CONTRACT AND DL.DC_ENGAGEMENT_ID = ERU.DC_ENGAGEMENT_ID AND ERU.IS_DELETED = 'F')
    JOIN DC_USERS USR ON (USR.USER_ID = ERU.DC_USER_ID AND USR.IS_DELETED = 'F')
    WHERE ERU.DC_ENGAGEMENT_ID = :dc_engagement_id AND ERU.DC_USER_ID = :dc_user_id AND USR.USER_ID = :dc_user_id
    """
        )
        .bindparams(dc_engagement_id=dc_engagement_id, dc_user_id=dc_user_id)
        .columns(
            booking_contract=Integer,
            closed_date=Date,
            completed_by=String,
            completion_type_id=Integer,
            cycle=Integer,
            dc_engagement_id=Integer,
            deliverable_desc=String,
            deliverable_id=Integer,
            due_date=Date,
            header_name=String,
            engagement_name=String,
            is_closed=Boolean,
            sort_date=Date,
            sub_task_id=Integer,
            subtask_desc=String,
            task_desc=String,
            task_id=Integer,
            task_status=String,
            cisco_cco_id=String,
        )
    )

    return query


def query_user_engagement_active_deliverables(
    dc_engagement_id: int, dc_user_id: int
) -> "TextualSelect":
    """
    Referred to as 'View 4 (Active)'
    """

    query = (
        text(
            """
    SELECT  DISTINCT
    DL.BOOKING_CONTRACT AS BOOKING_CONTRACT,
    DL.COMPLETED_CCO AS COMPLETED_BY,
    DL.COMPLETED_DATE::DATE AS CLOSED_DATE,
    DL.COMPLETED_ST IS NOT NULL AS IS_CLOSED,
    DL.COMPLETION_TYPE_ID AS COMPLETION_TYPE_ID,
    DL.DC_ENGAGEMENT_ID AS DC_ENGAGEMENT_ID,
    DL.DELIVERABLE_DESC AS DELIVERABLE_DESC,
    DL.DELIVERABLE_ID AS DELIVERABLE_ID,
    DL.DUE_DATE AS DUE_DATE,
    DL.ENGAGEMENT_NAME AS ENGAGEMENT_NAME,
    DL.HEADER_NAME AS HEADER_NAME,
    DL.INDEX_POS AS CYCLE,
    DL.SUB_TASK_ID AS SUB_TASK_ID,
    DL.SUBTASK_DESC AS SUBTASK_DESC,
    DL.TASK_DESC AS TASK_DESC,
    DL.TASK_ID AS TASK_ID,
    DL.TASK_STATUS AS TASK_STATUS,
    DL.VISIBILITY_DATE AS SORT_DATE,
    USR.CISCO_CCO_ID AS CISCO_CCO_ID
    
    FROM DC_DELIVERABLES_LIVE_ENG DL
    JOIN DC_ENGAGEMENT_TO_BOOKINGS_RESPONSIBLE_USER ERU
    ON (DL.BOOKING_CONTRACT = ERU.BOOKING_CONTRACT AND DL.DC_ENGAGEMENT_ID = ERU.DC_ENGAGEMENT_ID AND ERU.IS_DELETED = 'F')
    JOIN DC_USERS USR ON (USR.USER_ID = ERU.DC_USER_ID AND USR.IS_DELETED = 'F')
    WHERE ERU.DC_ENGAGEMENT_ID = :dc_engagement_id AND ERU.DC_USER_ID = :dc_user_id AND USR.USER_ID = :dc_user_id
    """
        )
        .bindparams(dc_engagement_id=dc_engagement_id, dc_user_id=dc_user_id)
        .columns(
            booking_contract=Integer,
            completed_by=String,
            closed_date=Date,
            is_closed=Boolean,
            completion_type_id=Integer,
            dc_engagement_id=Integer,
            deliverable_desc=String,
            deliverable_id=Integer,
            due_date=Date,
            engagement_name=String,
            header_name=String,
            cycle=Integer,
            sub_task_id=Integer,
            subtask_desc=String,
            task_desc=String,
            task_id=Integer,
            task_status=String,
            sort_date=Date,
            cisco_cco_id=String,
        )
    )

    return query


def make_completion_fk_membership_query(
    sub_task_id: int,
    booking_contract: int,
    dc_engagement_id: int,
    completion_type_id: int,
) -> "CompoundSelect":
    """
    Generate a query to check that a completion's FKs exist and are not is_deleted = 'T'
    """

    from api.v2.orm import (
        SDPSubTask,
        SDPTaskCompletionReason,
        V2BookingContracts,
        V2Engagement,
    )
    from api.v2.queries import QueryMembership

    query_members = (
        QueryMembership()
        .add_orm_membership(
            model=SDPSubTask,
            member_ids=[sub_task_id],
        )
        .add_orm_membership(
            model=V2BookingContracts,
            member_ids=[booking_contract],
        )
        .add_orm_membership(
            model=V2Engagement,
            member_ids=[dc_engagement_id],
        )
        .add_orm_membership(
            model=SDPTaskCompletionReason,
            member_ids=[completion_type_id],
        )
        .build()
    )

    return query_members
