
use schema CPS_DSCI_BR;
use schema CPS_DSCI_API;
create or replace  procedure assign_responsible_users(invalue VARCHAR, logged_user varchar, booking_contract integer)
	returns VARIANT
	language SQL
	strict
	as $$
        DECLARE
        found_user_cco varchar; -- validated member of engagement

        begin
            create or replace temporary table CPS_DSCI_STG.json_input_assignments as
                with json as (
                select parse_json(:invalue) as json_data
                )
                 select distinct
                                json.json_data:booking_contract::number          as booking_contract,
                                cert.value:dc_user_id::number               as dc_user_id,
                                cert.value:service_role_id::number          as service_role_id,
                                cert.value:sub_allocation_sw::float        as sub_allocation_sw,
                                cert.value:sub_allocation_hw::float        as sub_allocation_hw
                                from json , lateral flatten(input => json.json_data:assignments) cert;

            update DC_BOOKINGS_CONTRACTS_RESPONSIBLE_USERS c
            set c.IS_DELETED = 'T' , c.UPDATED_BY = :logged_user, c.UPDATE_DTM = current_timestamp
            from
            (
                    select ru.*
                    from DC_BOOKINGS_CONTRACTS_RESPONSIBLE_USERS ru left join CPS_DSCI_STG.json_input_assignments a on ( ru.BOOKING_CONTRACT=a.booking_contract and ru.DC_USER_ID=a.dc_user_id)
                    where ru.BOOKING_CONTRACT = :booking_contract and IS_DELETED = 'F' and a.BOOKING_CONTRACT is null
                       ) o
            where   c.DC_USER_ID = o.DC_USER_ID and c.BOOKING_CONTRACT = o.booking_contract;

            MERGE INTO DC_BOOKINGS_CONTRACTS_RESPONSIBLE_USERS c
            USING CPS_DSCI_STG.json_input_assignments  AS b ON      c.DC_USER_ID = b.DC_USER_ID and c.BOOKING_CONTRACT = b.booking_contract
                WHEN MATCHED THEN UPDATE SET c.SUB_ALLOCATION_HW =b.sub_allocation_hw,
                                             c.SUB_ALLOCATION_SW=b.sub_allocation_sw,
                                             c.SERVICE_ROLE_ID = b.service_role_id,
                                             c.UPDATED_BY= :logged_user,
                                             c.UPDATE_DTM=current_timestamp,
                                             c.IS_DELETED = 'F'
                WHEN NOT MATCHED THEN INSERT( BOOKING_CONTRACT,     DC_USER_ID,  SUB_ALLOCATION_HW,  SUB_ALLOCATION_SW, SERVICE_ROLE_ID,   CREATED_BY,            CREATE_DTM)
                                     VALUES ( b.booking_contract, b.dc_user_id,b.sub_allocation_hw,b.sub_allocation_sw , b.service_role_id , :logged_user,  current_timestamp);

        --really should return true or error and insert these into audit table
        RETURN OBJECT_CONSTRUCT('MESSAGE','SUCCESS','SQLID',SQLID,'rowcount',SQLROWCOUNT, 'invalue',:invalue);
        end;
$$;





use schema CPS_DSCI_API;

 call assign_responsible_users('{"booking_contract": 123456,"assignments": [ {"booking_contract": 123456,"dc_user_id": 4,"service_role_id": 1,"sub_allocation_sw": 0,"sub_allocation_hw": 0}, {"booking_contract": 123456,"dc_user_id": 7,"service_role_id": 2,"sub_allocation_sw": .75,"sub_allocation_hw": .67},{"booking_contract": 123456,"dc_user_id": 13,"service_role_id": 2,"sub_allocation_sw": .25,"sub_allocation_hw": .33}]}',
                               'alanzen@cisco.com',
                               123456)



 call assign_responsible_users('{"booking_contract": 123456,"assignments": [ {"booking_contract": 123456,"dc_user_id": 4,"service_role_id": 2,"sub_allocation_sw": .5,"sub_allocation_hw": .5}, ,{"booking_contract": 123456,"dc_user_id": 13,"service_role_id": 4,"sub_allocation_sw": .5,"sub_allocation_hw": .500000000}]}',
                               'alanzen@cisco.com',
                               123456)


 call assign_responsible_users('{"booking_contract": 123456,"assignments": [ {"booking_contract": 123456,"dc_user_id": 4,"service_role_id": 2,"sub_allocation_sw": 1,"sub_allocation_hw": 1}]}',
                               'alanzen@cisco.com',
                               123456)


 select ru.*
        from DC_BOOKINGS_CONTRACTS_RESPONSIBLE_USERS ru
        where ru.BOOKING_CONTRACT =123456 and IS_DELETED = 'F'