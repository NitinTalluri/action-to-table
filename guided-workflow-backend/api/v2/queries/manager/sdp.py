from sqlalchemy import Integer, String, TextualSelect, text

from api.v2.orm.json_varchar import JSONVarchar


def query_manager_sdp(booking_contract: int) -> "TextualSelect":
    """Make a query to get a list all SDP tasks, subtasks, and deliverables that are appropriate for a booking contract,
    considering pricing_type_id, buying_program_type_id, and service_type_id.
    Include a list of currently responsible users that have subtasks already scheduled
    (despite subtasks are completed or not)."""

    query = (
        text(
            """
        WITH sdp AS (
            SELECT 
                dl.booking_contract, 
                sub_task_id, 
                ARRAY_AGG(DISTINCT dc_user_id) AS dc_user_ids
            FROM 
                dc_deliverables_owed_scheduled_eng dl
                JOIN dc_engagement_to_bookings_responsible_user eru
                    ON (
                        dl.booking_contract = eru.booking_contract
                        AND dl.dc_engagement_id = eru.dc_engagement_id 
                        AND eru.is_deleted = 'F'
                    )
                JOIN dc_users usr 
                    ON (
                        usr.user_id = eru.dc_user_id 
                        AND usr.is_deleted = 'F'
                    )
            GROUP BY 
                dl.booking_contract, sub_task_id 
        )
        SELECT DISTINCT 
            c.booking_contract,
            core.deliverable_id,
            core.deliverable_desc,
            core.task_id,
            core.task_desc,
            core.sub_task_id,
            core.subtask_desc,
            core.anchor_date_id AS task_anchor_date_id,
            core.iterator_date_name AS task_cycle_iterator_name,
            core.anchor_date_name AS task_anchor_date_name,
            core.cycle_iterator_id AS task_cycle_iterator_id,
            core.due_date_offset AS due_date_offset,
            core.cycle_days AS cycle_days,
            TO_JSON(IFNULL(dc_user_ids, ARRAY_CONSTRUCT())) AS sdp_assigned_user_ids
        FROM  
            dc_bookings_contracts c
            JOIN dc_cisco_deliverables core
                ON (
                    core.pricing_type_id = c.sold_as_pricing_type_id
                    AND core.buying_program_type_id = c.buying_program_type_id
                    AND core.service_type_id = c.sold_as_service_type_id
                )
            LEFT JOIN dc_engagement_to_bookings_responsible_user eru
                ON (
                    c.booking_contract = eru.booking_contract 
                    AND eru.is_deleted = 'F'
                )
            LEFT JOIN dc_engagement_hdr h 
                ON (h.dc_engagement_id = eru.dc_engagement_id)
            LEFT JOIN sdp 
                ON (
                    sdp.booking_contract = c.booking_contract 
                    AND sdp.sub_task_id = core.sub_task_id
                )
        WHERE 
            c.booking_contract = :booking_contract
        ORDER BY 
            core.deliverable_id, core.task_id, core.sub_task_id
        """
        )
        .bindparams(booking_contract=booking_contract)
        .columns(
            booking_contract=Integer,
            deliverable_id=Integer,
            deliverable_desc=String,
            task_id=Integer,
            task_desc=String,
            sub_task_id=Integer,
            subtask_desc=String,
            task_anchor_date_id=Integer,
            task_cycle_iterator_name=String,
            task_anchor_date_name=String,
            task_cycle_iterator_id=Integer,
            due_date_offset=Integer,
            cycle_days=Integer,
            sdp_assigned_user_ids=JSONVarchar,
        )
    )

    return query
