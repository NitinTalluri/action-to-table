use schema CPS_DSCI_API;
use schema CPS_DSCI_BR;
create or replace  procedure get_booking_contracts(logged_user varchar, dc_engagement_id integer)
    RETURNS TABLE(json varchar)
	language SQL
	strict
	as $$
        DECLARE
        res RESULTSET default ( with booking as (
                        select c.BOOKING_CONTRACT,  c.ACCOUNT_NAME, c.AGREEMENT_START_DATE, c.AGREEMENT_END_DATE,
                               nvl(st.sold_as_service_NAME,'UNSET') as sold_as_service_name,
                               nvl(pm.PRICING_MODEL_NAME,'UNSET') as sold_as_pricing_model,
                               nvl(bp.BUYING_PROGRAM_NAME,'UNSET') as sold_as_buying_program,
                               eru.DC_ENGAGEMENT_ID,
                               eru.DC_USER_ID,
                               u.cisco_cco_id ,
                               case when u.cisco_cco_id = :logged_user   then 'T' else 'F' end as is_editable
                        from dc_BOOKINGS_CONTRACTS c
                            join DC_BOOKINGS_CONTRACTS_RESPONSIBLE_USERS ru on ( ru.BOOKING_CONTRACT=c.BOOKING_CONTRACT and ru.IS_DELETED = 'F')
                            join DC_USERS u on (u.USER_ID=ru.DC_USER_ID  and u.IS_DELETED='F')
                            join dc_ENGAGEMENT_TO_BOOKINGS_RESPONSIBLE_USER eru on (eru.BOOKING_CONTRACT=ru.BOOKING_CONTRACT and eru.DC_USER_ID=ru.DC_USER_ID and eru.IS_DELETED = 'F')
                            join dc_pricing_model pm on (pm.PRICING_type_id  = c.SOLD_AS_PRICING_TYPE_ID )
                            join dc_buying_programs bp on ( bp.BUYING_PROGRAM_TYPE_ID= c.BUYING_PROGRAM_TYPE_ID)
                            join dc_sold_as_service_types st on (c.SOLD_AS_SERVICE_TYPE_ID = st.service_type_id )
                            where eru.dc_engagement_id= :dc_engagement_id and  c.IS_DELETED = 'F' and eru.is_deleted ='F'  and ru.is_deleted ='F' and u.IS_DELETED = 'F'
                    ), contracts as (
                        select booking.BOOKING_CONTRACT, booking.DC_USER_ID, booking.DC_ENGAGEMENT_ID,
                            --   'managed_contracts' ,
                                    array_agg(distinct OBJECT_CONSTRUCT_KEEP_NULL(
                                           'contract_number', msc.contract_number,
                                           'allowed_service_levels', msc.allowed_SERVICE_LEVELS,
                                           'contract_name', msc.contract_name,
                                           'notes', msc.notes
                                        )) as managed_json_object

                                        from booking left join   dc_managed_service_contracts msc
                                                      on (
                                                                 msc.DC_USER_ID = booking.DC_USER_ID and
                                                                  msc.BOOKING_CONTRACT = booking.BOOKING_CONTRACT and
                                                                  msc.dc_engagement_id = booking.DC_ENGAGEMENT_ID and
                                                                 msc.IS_DELETED = 'F'

                                                          )
                        group by booking.DC_USER_ID, booking.DC_ENGAGEMENT_ID,booking.BOOKING_CONTRACT
                    )
                    select
                        TO_JSON(OBJECT_CONSTRUCT_KEEP_NULL(
                                'booking_contract' , booking.booking_contract,
                                'account_name'      , booking.account_name,
                                'agreement_start_date'    ,booking.agreement_start_date,
                                'agreement_end_date'  ,  booking.agreement_end_date,
                                'sold_as_service_name'    , booking.sold_as_service_name,
                                'sold_as_pricing_model'    , booking.sold_as_pricing_model,
                                'sold_as_buying_program' , booking.sold_as_buying_program,
                                'dc_engagement_id'          ,booking.DC_ENGAGEMENT_ID,
                                'responsible_users',array_agg(distinct OBJECT_CONSTRUCT_KEEP_NULL(
                                        'responsible_user'          , booking.DC_USER_ID,
                                        'responsible_user_cco'          , booking.cisco_cco_id,
                                         'is_block_owner', booking.is_editable,
                                                'managed_contracts' , OBJECT_CONSTRUCT_KEEP_NULL(
                                                    'contracts' ,contracts.managed_json_object
                                                    )
                                    )))) as json
                    from booking join contracts on (booking.BOOKING_CONTRACT=  contracts.BOOKING_CONTRACT and booking.DC_ENGAGEMENT_ID=  contracts.DC_ENGAGEMENT_ID and contracts.DC_USER_ID = booking.DC_USER_ID )
                           group by booking.booking_contract, booking.account_name, booking.agreement_start_date, booking.agreement_end_date,
                             booking.sold_as_service_name, booking.sold_as_pricing_model,booking.DC_ENGAGEMENT_ID,
                             booking.sold_as_buying_program
        );

    BEGIN
    RETURN TABLE(res);
    END;


$$;


