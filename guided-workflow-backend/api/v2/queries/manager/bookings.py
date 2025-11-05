from sqlalchemy import (
    Boolean,
    Date,
    Float,
    Integer,
    String,
    text,
)

from api.v2.orm.json_varchar import JSONVarchar


def query_unclaimed_bookings(look_ahead_days=180, id_threshold=20400000):
    """
    Query unclaimed bookings

    Notes
    -----

    We want to ensure some columns are 0 if null (booked_sw, booked_hw). This could be done in python
    but this leverages SQL.

    - nvl for booked_sw, booked_hw, calculated_sw, calculated_hw
    - Add properties for is_virtual, is_renewal into the query (not included if just using the model)

    agreement_end_date is the greater of agreement_end_date and extension_end_date

    Parameters
    ----------
    look_ahead_days
    id_threshold
        A 'magic' number to filter bookings for CXEA
    """

    query = (
        text(
            """
            WITH renewal_cte AS (
            SELECT child_booking_contract AS booking_contract,
            ARRAY_UNIQUE_AGG(parent_booking_contract) AS renewed_from
            FROM dc_bookings_contracts_lineage
            WHERE is_deleted = 'F'
            AND parent_booking_contract IS NOT NULL
            GROUP BY child_booking_contract
        ),
        extensions_cte AS (
            SELECT booking_contract as booking_contract, 
            COUNT(booking_contract) AS extended_count,
            MAX(extension_end_date) AS effective_end_date
            FROM DC_BOOKING_CONTRACTS_EXTENSIONS
            WHERE is_deleted = 'F'
            GROUP BY booking_contract
        ),
        disengagement_cte AS (
            SELECT booking_contract as booking_contract, true as is_disengaged
            FROM DC_WF_DISENGAGE
            WHERE is_deleted = 'F'
        ),
        is_cxea_cte AS (
            SELECT buying_program_type_id,
                    NVL(BUYING_PROGRAM_NAME ILIKE '%CXEA%SCALE%', FALSE) AS is_cxea_scale,
                    NVL(BUYING_PROGRAM_NAME ILIKE '%CXEA%', FALSE) AS is_cxea
            FROM DC_BUYING_PROGRAMS
                WHERE IS_DELETED = 'F'
        )
        SELECT bc.booking_contract,
                account_name,
                booked_sav_1,
                booked_sav_2,
                booked_sav_3,
                booked_theater_id,
                sold_as_service_type_id,
                sold_as_pricing_type_id,
                bc.buying_program_type_id,
                booking_contract_type_id,
                booked_usd,
                agreement_start_date,
                agreement_end_date,
                NVL(ext.effective_end_date, agreement_end_date) AS effective_end_date,
                booking_country,
                cam_revenue_usd,
                cam_cost_usd,
                souced_allocation AS sourced_allocation,
                booked_date,
                NVL(sold_as_sw_allocation, 0) AS booked_sw,
                NVL(sold_as_hw_allocation, 0) AS booked_hw,
                NVL(sold_as_sw_allocation, 0) + NVL(sold_as_hw_allocation, 0) AS allocation_fte_total,
                quote_for_audit,
                IFF(disengagement_cte.is_disengaged IS NOT NULL, disengagement_cte.is_disengaged, false) AS is_disengaged,
                IFF(bc.booking_contract < 0, true, false) AS is_virtual,
                bc.is_deleted,
                IFF(derived_new_renew IN ('NEW', 'RENEWAL', 'UPSELL'), derived_new_renew, NULL) AS derived_new_renew,
                IFF(ic.buying_program_type_id IS NOT NULL, ic.is_cxea, false) AS is_cxea,
                dc_engagement_id_default,
                r.renewed_from AS renewed_from,
                NVL(ext.extended_count, 0) AS extended_count,
                NVL(bc.sales_level_id, 0) AS sales_level_id,
                NVL(sl.node_level1, '') AS node_level1,
                NVL(sl.node_level2, '') AS node_level2,
                NVL(sl.node_level3, '') AS node_level3,
                NVL(sl.node_level4, '') AS node_level4,
                NVL(sl.node_segment, '') AS node_segment
                FROM DC_BOOKINGS_CONTRACTS bc
                LEFT JOIN renewal_cte r ON bc.booking_contract = r.booking_contract
                LEFT JOIN disengagement_cte ON bc.booking_contract = disengagement_cte.booking_contract
                LEFT JOIN extensions_cte ext ON bc.booking_contract = ext.booking_contract
                LEFT JOIN is_cxea_cte ic ON bc.buying_program_type_id = ic.buying_program_type_id
                LEFT JOIN dc_sales_level sl ON bc.sales_level_id = sl.sl_id
                WHERE bc.is_deleted = 'F' AND (bc.claimed_and_managed_by IS NULL OR ic.is_cxea_scale = true)
                AND (
                    (current_date <= dateadd('day', :look_ahead_days, agreement_end_date) 
                        AND bc.booking_contract >= :id_threshold)
                     OR
                    (bc.booking_contract < :id_threshold and  current_date < agreement_end_date)
                    ) 
                """
        )
        .bindparams(look_ahead_days=look_ahead_days, id_threshold=id_threshold)
        .columns(
            booking_contract=Integer,
            account_name=String,
            booked_sav_1=String,
            booked_sav_2=String,
            booked_sav_3=String,
            booked_theater_id=Integer,
            sold_as_service_type_id=Integer,
            sold_as_pricing_type_id=Integer,
            buying_program_type_id=Integer,
            booking_contract_type_id=Integer,
            booked_usd=Float,
            agreement_start_date=Date,
            agreement_end_date=Date,
            effective_end_date=Date,
            booking_country=String,
            cam_revenue_usd=Float,
            cam_cost_usd=Float,
            sourced_allocation=Float,
            booked_date=Date,
            booked_sw=Float,
            booked_hw=Float,
            allocation_fte_total=Float,
            calculated_sw=Float,
            calculated_hw=Float,
            quote_for_audit=String,
            is_disengaged=Boolean,
            is_virtual=Boolean,
            is_deleted=String,
            derived_new_renew=String,
            renewed_from=JSONVarchar,
            extended_count=Integer,
            sales_level_id=Integer,
            node_level1=String,
            node_level2=String,
            node_level3=String,
            node_level4=String,
            node_segment=String,
            is_cxea=Boolean,
            dc_engagement_id_default=Integer,
        )
    )
    return query


def query_claimed_bookings(dc_user_id: int):
    """
    Get a manager's claimed bookings

    Parameters
    ----------
    dc_user_id

    Returns
    -------

    Notes
    -----
    DC_BOOKINGS_CONTRACTS_RESPONSIBLE_USERS
        -  0 <= sub_allocation_sw <= 1
        -  0 <= sub_allocation_hw <= 1
        This should sum to 1 for each booking contract.

    DC_BOOKINGS_CONTRACTS
        total_allocation (not a real column) = sold_as_sw_allocation + sold_as_hw_allocation

    """

    query = (
        text(
            """
        WITH unique_org_users AS (
            SELECT distinct EMP_CCO_ID, EMP_NAME
            FROM ORGANIZATIONAL_HIERARCHY
        ),
        named_users_cte AS (
            SELECT CONCAT(EMP_CCO_ID, '@cisco.com') AS cisco_cco_id, EMP_NAME AS display_name
            FROM unique_org_users
        ),
        explicit_claims AS (
            SELECT booking_contract
            FROM DC_BOOKINGS_CONTRACTS
            WHERE is_deleted = 'F'
            AND claimed_and_managed_by = :user_id
        ),
        renewal_cte AS (
            SELECT child_booking_contract AS booking_contract,
            ARRAY_UNIQUE_AGG(parent_booking_contract) AS renewed_from
            FROM dc_bookings_contracts_lineage
            JOIN explicit_claims ON child_booking_contract = booking_contract
            WHERE is_deleted = 'F'
            AND parent_booking_contract IS NOT NULL
            GROUP BY child_booking_contract
        ),
        disengagement_cte AS (
            SELECT ec.booking_contract as booking_contract, true as is_disengaged
            FROM explicit_claims ec
            JOIN DC_WF_DISENGAGE dis ON (ec.booking_contract = dis.booking_contract AND dis.is_deleted = 'F')
        ),
        extensions_cte AS (
            SELECT booking_contract AS booking_contract,
            MAX(extension_end_date) AS effective_end_date,
             COUNT(booking_contract) AS extended_count
             
            FROM DC_BOOKING_CONTRACTS_EXTENSIONS
            WHERE is_deleted = 'F'
            GROUP BY booking_contract
            
        ),
        assignments_with_name_cte AS (
            SELECT ec.booking_contract AS booking_contract,
            users.user_id AS dc_user_id,
            uu.display_name AS display_name,
            NVL(sub_allocation_hw, 0) AS sub_allocation_hw,
            NVL(sub_allocation_sw, 0) AS sub_allocation_sw,
            NVL(service_role_id, 1) AS service_role_id,
            eru.dc_engagement_id AS dc_engagement_id,
            hdr.engagement_name AS engagement_name
            
            
            FROM explicit_claims ec
            JOIN dc_bookings_contracts_responsible_users ru ON
              (ec.booking_contract = ru.booking_contract
                AND ru.is_deleted = 'F')
            LEFT JOIN dc_engagement_to_bookings_responsible_user eru ON
                (ru.booking_contract = eru.booking_contract
                AND eru.dc_user_id = ru.dc_user_id
                AND eru.is_deleted = 'F')
            JOIN dc_engagement_hdr hdr ON
                (eru.dc_engagement_id = hdr.dc_engagement_id
                AND hdr.is_deleted = 'F')
            JOIN dc_users users ON
                (eru.dc_user_id = users.user_id
                AND users.is_deleted = 'F')
            LEFT JOIN named_users_cte uu ON (users.cisco_cco_id = uu.cisco_cco_id)
        ),
        bc_assignments AS (
            SELECT booking_contract,
            TO_JSON(ARRAY_AGG(
                OBJECT_CONSTRUCT_KEEP_NULL(
                    'booking_contract', booking_contract,
                    'dc_user_id', dc_user_id,
                    'sub_allocation_hw', sub_allocation_hw,
                    'sub_allocation_sw', sub_allocation_sw,
                    'service_role_id', service_role_id,
                    'display_name', NVL(display_name, ''),
                    'dc_engagement_id', dc_engagement_id,
                    'engagement_name', engagement_name
                )
            )) AS assignments
            FROM assignments_with_name_cte
            GROUP BY booking_contract
        ),
        is_cxea_cte AS (
            SELECT buying_program_type_id, true as is_cxea
            FROM DC_BUYING_PROGRAMS
                WHERE  BUYING_PROGRAM_NAME ILIKE '%CXEA%' AND IS_DELETED = 'F'
        ),
        sdp_onboarding_status AS (
        SELECT BOOLOR_AGG(cd.sub_task_id IS NOT NULL)  has_complete_tasks,
               BOOLAND_AGG(cd.sub_task_id IS NOT NULL) has_all_tasks_completed,
               sd.booking_contract
          FROM dc_deliverables_owed_scheduled_eng sd
          LEFT JOIN dc_completed_deliverables cd
            ON (cd.sub_task_id = sd.sub_task_id AND cd.booking_contract = sd.booking_contract AND
                cd.cycle_iterator = sd.index_pos AND cd.dc_engagement_id = sd.dc_engagement_id AND
                cd.is_deleted = 'F')
        -- Initial IB Reconciliation
         WHERE deliverable_id = 3
         GROUP BY sd.booking_contract
        ),
        renewed AS (
        SELECT DISTINCT parent_booking_contract booking_contract
          FROM dc_bookings_contracts_lineage
         WHERE is_deleted = 'F'
           AND parent_booking_contract != child_booking_contract)
        SELECT bc.booking_contract,
        account_name,
        booked_sav_1,
        booked_sav_2,
        booked_sav_3,
        booked_theater_id,
        sold_as_service_type_id,
        sold_as_pricing_type_id,
        bc.buying_program_type_id,
        booking_contract_type_id,
        booked_usd,
        agreement_start_date,
        agreement_end_date,
        NVL(ext.effective_end_date, agreement_end_date) AS effective_end_date,
        booking_country,
        cam_revenue_usd,
        cam_cost_usd,
        souced_allocation AS sourced_allocation,
        booked_date,
        NVL(sold_as_sw_allocation, 0) AS booked_sw,
        NVL(sold_as_hw_allocation, 0) AS booked_hw,
        NVL(ib_calc_sw_allocation, 0) AS calculated_sw,
        NVL(ib_calc_hw_allocation, 0) AS calculated_hw,
        NVL(sold_as_sw_allocation, 0) + NVL(sold_as_hw_allocation, 0) AS allocation_fte_total,
        NVL(allocation_fte_sw_ratio, 0) AS allocation_fte_sw_ratio,
        NVL(allocation_fte_hw_ratio, 0) AS allocation_fte_hw_ratio,
        quote_for_audit,
        IFF(ic.is_cxea IS NOT NULL, ic.is_cxea, false) AS is_cxea,
        IFF(disengagement_cte.is_disengaged IS NOT NULL, disengagement_cte.is_disengaged, false) AS is_disengaged,
        IFF(bc.booking_contract < 0, true, false) AS is_virtual,
        bc.is_deleted,
        claimed_and_managed_by,
        IFF(derived_new_renew IN ('NEW', 'RENEWAL', 'UPSELL'), derived_new_renew, NULL) AS derived_new_renew,
        r.renewed_from AS renewed_from,
        NVL(ext.extended_count, 0) AS extended_count,
        NVL(bc_assignments.assignments, TO_JSON(ARRAY_CONSTRUCT())) AS assignments,
        CASE WHEN rn.booking_contract IS NOT NULL THEN 'Renewed'
             WHEN so.has_all_tasks_completed IS NULL THEN 'New'
             WHEN so.has_all_tasks_completed AND CURRENT_DATE() > DATEADD(DAY, -90, agreement_end_date) THEN 'Renewal Readiness'
             WHEN so.has_all_tasks_completed THEN 'Lifecycle'
             WHEN NOT so.has_all_tasks_completed THEN 'Onboarding'
             ELSE 'Unknown' END AS delivery_status,
        dc_engagement_id_default,
        NVL(bc.SALES_LEVEL_ID, 0) as sales_level_id,
        NVL(sl.node_level1, '') AS node_level1,
        NVL(sl.node_level2, '') AS node_level2,
        NVL(sl.node_level3, '') AS node_level3,
        NVL(sl.node_level4, '') AS node_level4,
        NVL(sl.node_segment, '') AS node_segment
        FROM DC_BOOKINGS_CONTRACTS bc
        LEFT JOIN renewal_cte r ON bc.booking_contract = r.booking_contract
        LEFT JOIN dc_engagement_hdr hdr ON (bc.dc_engagement_id = hdr.dc_engagement_id AND hdr.is_deleted = 'F')
        LEFT JOIN disengagement_cte ON bc.booking_contract = disengagement_cte.booking_contract
        LEFT JOIN extensions_cte ext ON bc.booking_contract = ext.booking_contract
        LEFT JOIN bc_assignments ON bc.booking_contract = bc_assignments.booking_contract
        LEFT JOIN is_cxea_cte ic ON bc.buying_program_type_id = ic.buying_program_type_id
        LEFT JOIN sdp_onboarding_status so ON so.booking_contract = bc.booking_contract
        LEFT JOIN renewed rn ON rn.booking_contract = bc.booking_contract
        LEFT JOIN DC_SALES_LEVEL sl ON bc.sales_level_id = sl.sl_id
        WHERE bc.claimed_and_managed_by = :user_id and bc.is_deleted = 'F'
        """
        )
        .bindparams(user_id=dc_user_id)
        .columns(
            booking_contract=Integer,
            account_name=String,
            booked_sav_1=String,
            booked_sav_2=String,
            booked_sav_3=String,
            booked_theater_id=Integer,
            sold_as_service_type_id=Integer,
            sold_as_pricing_type_id=Integer,
            buying_program_type_id=Integer,
            booking_contract_type_id=Integer,
            booked_usd=Float,
            agreement_start_date=Date,
            agreement_end_date=Date,
            effective_end_date=Date,
            booking_country=String,
            cam_revenue_usd=Float,
            cam_cost_usd=Float,
            sourced_allocation=Float,
            booked_date=Date,
            booked_sw=Float,
            booked_hw=Float,
            calculated_sw=Float,
            calculated_hw=Float,
            allocation_fte_total=Float,
            allocation_fte_sw_ratio=Float,
            allocation_fte_hw_ratio=Float,
            quote_for_audit=String,
            is_cxea=Boolean,
            is_disengaged=Boolean,
            is_virtual=Boolean,
            is_deleted=String,
            claimed_and_managed_by=Integer,
            derived_new_renew=String,
            renewed_from=JSONVarchar,
            extended_count=Integer,
            assignments=JSONVarchar,
            delivery_status=String,
            sales_level_id=Integer,
            node_level1=String,
            node_level2=String,
            node_level3=String,
            node_level4=String,
            node_segment=String,
        )
    )

    return query


def query_claimed_booking(booking_contract: int):
    """
    Get a claimed booking by booking contract

    Parameters
    ----------
    """

    query = (
        text(
            """
        WITH renewal_cte AS (
            SELECT child_booking_contract AS booking_contract,
            ARRAY_UNIQUE_AGG(parent_booking_contract) AS renewed_from
            FROM dc_bookings_contracts_lineage
            WHERE is_deleted = 'F'
            AND child_booking_contract = :booking_contract
            AND parent_booking_contract IS NOT NULL
            GROUP BY child_booking_contract
        ),
        unique_org_users AS (
            SELECT distinct EMP_CCO_ID, EMP_NAME
            FROM ORGANIZATIONAL_HIERARCHY
        ),
        unique_users AS (
            SELECT CONCAT(EMP_CCO_ID, '@cisco.com') AS cisco_cco_id, EMP_NAME AS display_name
            FROM unique_org_users
        ),
        assignments_with_name_cte AS (
            SELECT ru.booking_contract AS booking_contract,
            eru.dc_user_id AS dc_user_id,
            uu.display_name AS display_name,
            NVL(sub_allocation_hw, 0) AS sub_allocation_hw,
            NVL(sub_allocation_sw, 0) AS sub_allocation_sw,
            NVL(service_role_id, 1) AS service_role_id,
            eru.dc_engagement_id AS dc_engagement_id,
            hdr.engagement_name AS engagement_name
            
            FROM dc_bookings_contracts_responsible_users ru
            JOIN dc_users users ON (dc_user_id = users.user_id AND users.is_deleted = 'F')
            LEFT JOIN dc_engagement_to_bookings_responsible_user eru ON (ru.booking_contract = eru.booking_contract
                AND eru.dc_user_id = ru.dc_user_id 
                AND eru.is_deleted = 'F'
            )
            JOIN dc_engagement_hdr hdr ON (eru.dc_engagement_id = hdr.dc_engagement_id AND hdr.is_deleted = 'F')
            LEFT JOIN unique_users uu ON (users.cisco_cco_id = uu.cisco_cco_id)
            WHERE ru.booking_contract = :booking_contract AND ru.is_deleted = 'F'
        ),
        bc_assignments AS (
            SELECT booking_contract,
            TO_JSON(ARRAY_AGG(
                OBJECT_CONSTRUCT_KEEP_NULL(
                    'booking_contract', booking_contract,
                    'dc_user_id', dc_user_id,
                    'sub_allocation_hw', sub_allocation_hw,
                    'sub_allocation_sw', sub_allocation_sw,
                    'service_role_id', service_role_id,
                    'display_name', NVL(display_name, ''),
                    'dc_engagement_id', dc_engagement_id,
                    'engagement_name', engagement_name
                )
            )) AS assignments
            FROM assignments_with_name_cte
            GROUP BY booking_contract
        ),
        extensions_cte AS (
            SELECT booking_contract as booking_contract,
             COUNT(booking_contract) AS extended_count,
            MAX(extension_end_date) AS effective_end_date
            FROM DC_BOOKING_CONTRACTS_EXTENSIONS
            WHERE is_deleted = 'F'
            AND booking_contract = :booking_contract
            GROUP BY booking_contract
        ),
        
        is_cxea_cte AS (
            SELECT buying_program_type_id, true as is_cxea
            FROM DC_BUYING_PROGRAMS
                WHERE  BUYING_PROGRAM_NAME ILIKE '%CXEA%' AND IS_DELETED = 'F'
        ),
        sdp_onboarding_status AS (
        SELECT BOOLOR_AGG(cd.sub_task_id IS NOT NULL)  has_complete_tasks,
               BOOLAND_AGG(cd.sub_task_id IS NOT NULL) has_all_tasks_completed,
               sd.booking_contract
          FROM dc_deliverables_owed_scheduled_eng sd
          LEFT JOIN dc_completed_deliverables cd
            ON (cd.sub_task_id = sd.sub_task_id AND cd.booking_contract = sd.booking_contract AND
                cd.cycle_iterator = sd.index_pos AND cd.dc_engagement_id = sd.dc_engagement_id AND
                cd.is_deleted = 'F')
        -- Initial IB Reconciliation
         WHERE deliverable_id = 3
         GROUP BY sd.booking_contract
        ),
        renewed AS (
        SELECT DISTINCT parent_booking_contract booking_contract
          FROM dc_bookings_contracts_lineage
         WHERE is_deleted = 'F'
           AND parent_booking_contract != child_booking_contract)
        SELECT
            DISTINCT
            bc.booking_contract,
        account_name,
        booked_sav_1,
        booked_sav_2,
        booked_sav_3,
        booked_theater_id,
        sold_as_service_type_id,
        sold_as_pricing_type_id,
        bc.buying_program_type_id,
        booking_contract_type_id,
        booked_usd,
        agreement_start_date,
        agreement_end_date,
        NVL(ext.effective_end_date, agreement_end_date) AS effective_end_date,
        booking_country,
        cam_revenue_usd,
        cam_cost_usd,
        souced_allocation AS sourced_allocation,
        booked_date,
        NVL(sold_as_sw_allocation, 0) AS booked_sw,
        NVL(sold_as_hw_allocation, 0) AS booked_hw,
        NVL(sold_as_sw_allocation, 0) + NVL(sold_as_hw_allocation, 0) AS allocation_fte_total,
        NVL(ib_calc_sw_allocation, 0) AS calculated_sw,
        NVL(ib_calc_hw_allocation, 0) AS calculated_hw,
        NVL(allocation_fte_sw_ratio, 0) as allocation_fte_sw_ratio,
        NVL(allocation_fte_hw_ratio, 0) as allocation_fte_hw_ratio,
        quote_for_audit,
        IFF(ic.buying_program_type_id IS NOT NULL, ic.is_cxea, false) AS is_cxea,
        IFF(dis.booking_contract IS NOT NULL, true, false) AS is_disengaged,
        IFF(bc.booking_contract < 0, true, false) AS is_virtual,
        bc.is_deleted,
        claimed_and_managed_by,
        IFF(derived_new_renew IN ('NEW', 'RENEWAL', 'UPSELL'), derived_new_renew, NULL) AS derived_new_renew,
        r.renewed_from AS renewed_from,
        NVL(ext.extended_count, 0) AS extended_count,
        NVL(bc_assignments.assignments, TO_JSON(ARRAY_CONSTRUCT())) AS assignments,
        CASE WHEN rn.booking_contract IS NOT NULL THEN 'Renewed'
             WHEN so.has_all_tasks_completed IS NULL THEN 'New'
             WHEN so.has_all_tasks_completed AND CURRENT_DATE() > DATEADD(DAY, -90, agreement_end_date) THEN 'Renewal Readiness'
             WHEN so.has_all_tasks_completed THEN 'Lifecycle'
             WHEN NOT so.has_all_tasks_completed THEN 'Onboarding'
             ELSE 'Unknown' END AS delivery_status,
        dc_engagement_id_default,
        NVL(bc.sales_level_id, 0) AS sales_level_id,
        NVL(sl.node_level1, '') AS node_level1,
        NVL(sl.node_level2, '') AS node_level2,
        NVL(sl.node_level3, '') AS node_level3,
        NVL(sl.node_level4, '') AS node_level4,
        NVL(sl.node_segment, '') AS node_segment      
        FROM DC_BOOKINGS_CONTRACTS bc
        LEFT JOIN renewal_cte r ON bc.booking_contract = r.booking_contract
        LEFT JOIN dc_wf_disengage dis ON (bc.booking_contract = dis.booking_contract AND dis.is_deleted = 'F')
        LEFT JOIN extensions_cte ext ON bc.booking_contract = ext.booking_contract
        LEFT JOIN bc_assignments ON bc.booking_contract = bc_assignments.booking_contract
        LEFT JOIN is_cxea_cte ic ON bc.buying_program_type_id = ic.buying_program_type_id
        LEFT JOIN sdp_onboarding_status so ON so.booking_contract = bc.booking_contract
        LEFT JOIN renewed rn ON rn.booking_contract = bc.booking_contract
        LEFT JOIN dc_sales_level sl ON bc.sales_level_id = sl.sl_id        
        WHERE bc.booking_contract = :booking_contract and bc.is_deleted = 'F'
        """
        )
        .bindparams(booking_contract=booking_contract)
        .columns(
            booking_contract=Integer,
            account_name=String,
            booked_sav_1=String,
            booked_sav_2=String,
            booked_sav_3=String,
            booked_theater_id=Integer,
            sold_as_service_type_id=Integer,
            sold_as_pricing_type_id=Integer,
            buying_program_type_id=Integer,
            booking_contract_type_id=Integer,
            booked_usd=Float,
            agreement_start_date=Date,
            agreement_end_date=Date,
            effective_end_date=Date,
            booking_country=String,
            cam_revenue_usd=Float,
            cam_cost_usd=Float,
            sourced_allocation=Float,
            booked_date=Date,
            booked_sw=Float,
            booked_hw=Float,
            calculated_sw=Float,
            calculated_hw=Float,
            allocation_fte_total=Float,
            allocation_fte_sw_ratio=Float,
            allocation_fte_hw_ratio=Float,
            quote_for_audit=String,
            is_cxea=Boolean,
            is_disengaged=Boolean,
            is_virtual=Boolean,
            is_deleted=String,
            claimed_and_managed_by=Integer,
            derived_new_renew=String,
            renewed_from=JSONVarchar,
            extended_count=Integer,
            assignments=JSONVarchar,
            delivery_status=String,
            sales_level_id=Integer,
            node_level1=String,
            node_level2=String,
            node_level3=String,
            node_level4=String,
            node_segment=String,
        )
    )

    return query


def query_available_to_renew_from():
    """
    Get a list of booking contracts that are available to be renewed from.
    The only requirement is that they are not virtual
    """

    query = text(
        """
WITH unique_org_users      AS (SELECT DISTINCT EMP_CCO_ID, EMP_NAME
                                   FROM ORGANIZATIONAL_HIERARCHY),
     named_org_users       AS (SELECT CONCAT( EMP_CCO_ID, '@cisco.com' ) AS cisco_cco_id, EMP_NAME AS display_name
                                   FROM unique_org_users),
     named_dc_users        AS (SELECT users.cisco_cco_id AS cisco_cco_id,
                                      users.user_id      AS user_id,
                                      nu.display_name    AS display_name
                                   FROM dc_users users
                                            JOIN named_org_users nu ON (users.cisco_cco_id = nu.cisco_cco_id)
                                   WHERE users.is_deleted = 'F'),
     has_renewal_cte       AS
         (SELECT dc_bookings_contracts_lineage.parent_booking_contract AS parent_booking_contract,
                 dc_bookings_contracts_lineage.child_booking_contract  AS child_booking_contract
              FROM dc_bookings_contracts_lineage
              WHERE dc_bookings_contracts_lineage.is_deleted = 'F'
                AND dc_bookings_contracts_lineage.parent_booking_contract IS NOT NULL
                AND dc_bookings_contracts_lineage.child_booking_contract IS NOT NULL),
     engagements_cte       AS
         (SELECT dc_engagement_to_bookings_responsible_user.booking_contract AS booking_contract,
                 ARRAY_AGG( DISTINCT
                            OBJECT_CONSTRUCT_KEEP_NULL(
                                    'dc_engagement_id', dc_engagement_to_bookings_responsible_user.dc_engagement_id,
                                    'engagement_name', engagement_name
                            )
                 )                                                           AS engagements
              FROM dc_engagement_to_bookings_responsible_user
                       JOIN dc_engagement_hdr ON dc_engagement_to_bookings_responsible_user.dc_engagement_id =
                                                 dc_engagement_hdr.dc_engagement_id AND
                                                 dc_engagement_hdr.is_deleted = 'F'
              WHERE dc_engagement_to_bookings_responsible_user.is_deleted = 'F'
              GROUP BY dc_engagement_to_bookings_responsible_user.booking_contract),
     booking_named_ru      AS (SELECT ru.booking_contract                                              AS booking_contract,
                                      ARRAY_DISTINCT( ARRAY_COMPACT( ARRAY_AGG( NDU.display_name ) ) ) AS employee_names

                                   FROM dc_bookings_contracts_responsible_users ru
                                            JOIN named_dc_users ndu ON (ru.dc_user_id = ndu.user_id)
                                   WHERE ru.is_deleted = 'F'
                                   GROUP BY ru.booking_contract),
     booking_named_claimed AS (SELECT bc.booking_contract AS booking_contract,
                                      ndu.display_name    AS display_name
                                   FROM dc_bookings_contracts bc
                                            JOIN named_dc_users ndu ON (bc.claimed_and_managed_by = ndu.user_id AND
                                                                        bc.claimed_and_managed_by IS NOT NULL)
                                   WHERE bc.is_deleted = 'F'),
     extensions_cte AS (
            SELECT booking_contract as booking_contract,
             COUNT(booking_contract) AS extended_count,
            MAX(extension_end_date) AS effective_end_date
            FROM DC_BOOKING_CONTRACTS_EXTENSIONS
            WHERE is_deleted = 'F'
            GROUP BY booking_contract
     )

SELECT dc_bookings_contracts.booking_contract,
       dc_bookings_contracts.account_name,
       dc_bookings_contracts.agreement_start_date,
       dc_bookings_contracts.agreement_end_date,
       NVL(ext.effective_end_date, agreement_end_date) AS effective_end_date,
       dc_bookings_contracts.booking_contract_type_id,
       dc_bookings_contracts.buying_program_type_id,
       dc_bookings_contracts.sold_as_service_type_id,
       dc_bookings_contracts.sold_as_pricing_type_id,
       booking_named_claimed.display_name as manager_name,
       booking_named_ru.employee_names,
       engagements_cte.engagements                                                                AS engagements,
       ARRAY_COMPACT( ARRAY_AGG( has_renewal_cte.child_booking_contract )
                                 WITHIN GROUP (ORDER BY has_renewal_cte.child_booking_contract) ) AS renewed_from,
       NVL(dc_bookings_contracts.sales_level_id, 0) AS sales_level_id,
       NVL(sl.node_level1, '') AS node_level1,
       NVL(sl.node_level2, '') AS node_level2,
       NVL(sl.node_level3, '') AS node_level3,
       NVL(sl.node_level4, '') AS node_level4,
       NVL(sl.node_segment, '') AS node_segment
    FROM dc_bookings_contracts
             LEFT JOIN has_renewal_cte
                             ON dc_bookings_contracts.booking_contract = has_renewal_cte.parent_booking_contract
             LEFT JOIN engagements_cte
                             ON dc_bookings_contracts.booking_contract = engagements_cte.booking_contract
             LEFT JOIN booking_named_ru
                             ON dc_bookings_contracts.booking_contract = booking_named_ru.booking_contract
             LEFT JOIN booking_named_claimed
                             ON dc_bookings_contracts.booking_contract = booking_named_claimed.booking_contract
             LEFT JOIN extensions_cte ext ON dc_bookings_contracts.booking_contract = ext.booking_contract
             LEFT JOIN dc_sales_level sl ON dc_bookings_contracts.sales_level_id = sl.sl_id
             
    WHERE dc_bookings_contracts.is_deleted = 'F'
    AND dc_bookings_contracts.BOOKING_CONTRACT > 0
    GROUP BY dc_bookings_contracts.booking_contract, dc_bookings_contracts.account_name,
             dc_bookings_contracts.agreement_start_date, dc_bookings_contracts.agreement_end_date,
             dc_bookings_contracts.booking_contract_type_id, dc_bookings_contracts.buying_program_type_id,
             dc_bookings_contracts.sold_as_service_type_id, dc_bookings_contracts.sold_as_pricing_type_id,
             dc_bookings_contracts.claimed_and_managed_by, engagements_cte.engagements,
             booking_named_claimed.display_name, booking_named_ru.employee_names, effective_end_date, dc_bookings_contracts.sales_level_id, sl.node_level1, sl.node_level2, sl.node_level3, sl.node_level4, sl.node_segment

        """
    ).columns(
        booking_contract=Integer,
        account_name=String,
        agreement_start_date=Date,
        agreement_end_date=Date,
        effective_end_date=Date,
        booking_contract_type_id=Integer,
        buying_program_type_id=Integer,
        sold_as_service_type_id=Integer,
        sold_as_pricing_type_id=Integer,
        manager_name=String,
        employee_names=JSONVarchar,
        engagements=JSONVarchar,
        renewed_from=JSONVarchar,
        sales_level_id=Integer,
        node_level1=String,
        node_level2=String,
        node_level3=String,
        node_level4=String,
        node_segment=String,
    )
    return query
