import datetime as dt
import json
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy import Integer, String, bindparam, text
from sqlmodel import select
from starlette.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
)

from api.dependencies import GetSessionDep, UserRequest
from api.v2.models import (
    V2BookingContract_POST,
    V2BookingContractRead,
    V2ContractCreate,
    V2ContractRead,
    V2MonitorContract_Update_Create,
    V2Responsible_User_Contract_Link,
)
from api.v2.orm import (
    V2BookingToEngagementResponsibleUser,
    V2CamEngagement,
    V2Contract,
    V2Engagement,
    V2MonitorContracts,
    V2User,
)
from api.v2.queries import (
    GET_logged_user,
    query_engagement_booking_contracts,
    query_engagement_contracts,
    query_referenced_engagement_id,
    query_referenced_user,
    query_users_engagements,
)

router = APIRouter()
logger = logging.getLogger("api")


@router.get("/{dc_engagement_id}", response_model=list[V2ContractRead])
def get_engagement_contracts_v2(
    req: UserRequest,
    dc_engagement_id: int,
    session: GetSessionDep,
    logged_user: Optional[str] = None,
):
    """Get the contracts for an engagement."""
    logged_user = GET_logged_user(req, logged_user)

    db_user_query = query_referenced_user(req, logged_user)
    db_user = session.exec(db_user_query).one()
    db_engagement_query = query_referenced_engagement_id(
        dc_engagement_id, db_user.user_id
    )
    db_engagement_id = session.exec(db_engagement_query).one_or_none()
    if not db_engagement_id:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="You are not authorized to view contracts on this engagement",
        )
    db_engagement_query = query_engagement_contracts(
        db_engagement_id, db_user.cisco_cco_id
    )
    db_engagement = session.exec(db_engagement_query).all()
    return db_engagement


@router.post("/{dc_engagement_id}", response_model=None, status_code=HTTP_201_CREATED)
def create_contracts_v2(
    data: V2ContractCreate,
    dc_engagement_id: int,
    req: UserRequest,
    session: GetSessionDep,
    logged_user: Optional[str] = None,
) -> V2Contract:
    """Create a new contract for an engagement."""
    logged_user = GET_logged_user(req, logged_user)
    db_user_query = query_referenced_user(req, logged_user)
    db_user = session.exec(db_user_query).one_or_none()
    db_engagement_query = query_referenced_engagement_id(
        dc_engagement_id, db_user.user_id
    )
    db_engagement_id = session.exec(db_engagement_query).one_or_none()
    if not db_engagement_id:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="You are not authorized to add contracts on this engagement",
        )
    new_contract = V2Contract(**data.dict(exclude_unset=True))

    existing_contract = (
        (
            session.execute(
                select(V2Contract)
                .join(V2Engagement)
                .join(V2CamEngagement)
                .join(V2User)
                .where(V2User.cisco_cco_id == logged_user)
                .where(V2Engagement.dc_engagement_id == dc_engagement_id)
                .where(V2Contract.contract_number == new_contract.contract_number)
            )
        )
        .scalars()
        .one_or_none()
    )

    if existing_contract is None:
        new_contract.dc_engagement_id = dc_engagement_id
        new_contract.created_by = logged_user
        new_contract.create_dtm = dt.datetime.now()
        for field, value in data.dict(exclude_unset=True).items():
            setattr(new_contract, field, value)
        session.add(new_contract)
        session.commit()
        session.refresh(new_contract)
        return new_contract
    elif existing_contract.is_deleted == "T":
        existing_contract.is_deleted = "F"
        existing_contract.updated_dtm = dt.datetime.now()
        existing_contract.updated_by = logged_user
        for field, value in data.dict(exclude_unset=True).items():
            setattr(existing_contract, field, value)
        session.add(existing_contract)
        session.commit()
        session.refresh(existing_contract)
        return existing_contract
    else:
        raise HTTPException(status_code=409, detail="Contract number already exists")


@router.patch("/{dc_engagement_id}", response_model=None, status_code=HTTP_201_CREATED)
def update_contracts_v2(
    data: V2ContractCreate,
    dc_engagement_id: int,
    req: UserRequest,
    session: GetSessionDep,
    logged_user: Optional[str] = None,
) -> V2Contract:
    """Update a contract for an engagement."""
    logged_user = GET_logged_user(req, logged_user)
    existing_contract = (
        (
            session.execute(
                select(V2Contract)
                .join(V2Engagement)
                .join(V2CamEngagement)
                .join(V2User)
                .where(V2User.cisco_cco_id == logged_user)
                .where(V2Engagement.dc_engagement_id == dc_engagement_id)
                .where(V2Contract.contract_number == data.contract_number)
            )
        )
        .scalars()
        .one_or_none()
    )
    if existing_contract is None:
        raise HTTPException(status_code=409, detail="Contract number does not exist")
    else:
        existing_contract.is_deleted = "F"
        existing_contract.updated_dtm = dt.datetime.now()
        existing_contract.updated_by = logged_user
        for field, value in data.dict(exclude_unset=True).items():
            setattr(existing_contract, field, value)
        session.add(existing_contract)
        session.commit()
        session.refresh(existing_contract)
        return existing_contract


@router.delete("/{engagement_id}/{contract_number}")
def delete_contract(
    engagement_id: int,
    contract_number: int,
    req: UserRequest,
    session: GetSessionDep,
    logged_user: Optional[str] = None,
):
    """Delete a contract from an engagement."""
    # TODO make sure they own it
    logged_user = GET_logged_user(req, logged_user)
    db_contract = (
        (
            session.execute(
                select(V2Contract)
                .join(V2Engagement)
                .join(V2CamEngagement)
                .join(V2User)
                .where(V2User.cisco_cco_id == logged_user)
                .where(V2Engagement.dc_engagement_id == engagement_id)
                .where(V2Contract.contract_number == contract_number)
            )
        )
        .scalars()
        .one_or_none()
    )
    if not db_contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    logger.info(db_contract)
    db_contract.soft_delete(logged_user, session)
    return db_contract


@router.get("/monitor/{dc_engagement_id}")
def extract_contracts_v2(
    dc_engagement_id: int,
    req: UserRequest,
    session: GetSessionDep,
    logged_user: Optional[str] = None,
):
    """Get the tagsets and related tags for an engagement"""
    logged_user = GET_logged_user(req, logged_user)
    user_engagements_query = query_users_engagements(logged_user).where(
        V2Engagement.dc_engagement_id == dc_engagement_id
    )
    user_engagement = session.exec(user_engagements_query).one_or_none()
    if not user_engagement:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND, detail="Engagement not found"
        )

    get_tags_query = text(
        """with booking as (
            select c.contract_number, c.monitor_type_id , t.MONITOR_REASON , c.monitor_notes, c.CREATED_BY
            from dc_monitor_service_contracts c join DC_CONTRACT_MONITOR_TYPES t on ( c.monitor_type_id=t.monitor_type_id  )
            where dc_engagement_id=  :dc_engagement_id and c.is_deleted='F'
        )
        select
                TO_JSON(OBJECT_CONSTRUCT_KEEP_NULL(
                                        'contract_number' , booking.contract_number,
                                       'monitor_type_id'      , booking.monitor_type_id,
                                       'monitor_reason'    ,booking.monitor_reason,
                                       'monitor_notes'  ,  booking.monitor_notes,
                                       'created_by'    , booking.CREATED_BY
                    ))
          from booking"""
    ).bindparams(
        bindparam("dc_engagement_id", dc_engagement_id, type_=Integer),
    )
    tags = session.execute(get_tags_query).scalars().fetchall()
    res = []

    if not tags:
        return res

    for r in tags:
        res.append(json.loads(r))
    return res


@router.post(
    "/monitor/{dc_engagement_id}", response_model=None, status_code=HTTP_201_CREATED
)
def create_unmanaged_contracts_v2(
    data: V2MonitorContract_Update_Create,
    dc_engagement_id: int,
    req: UserRequest,
    session: GetSessionDep,
    logged_user: Optional[str] = None,
):
    logged_user = GET_logged_user(req, logged_user)
    user = session.exec(
        select(V2User)
        .join(V2CamEngagement)
        .where(V2User.cisco_cco_id == logged_user)
        .where(V2CamEngagement.dc_engagement_id == dc_engagement_id)
    ).one_or_none()
    if not user:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="You are not authorized to add contracts on this engagement",
        )

    new_contract = V2MonitorContracts(**data.dict(exclude_unset=True))
    existing_contract = (
        (
            session.execute(
                select(V2MonitorContracts)
                .join(V2Engagement)
                .join(V2CamEngagement)
                .join(V2User)
                .where(V2User.cisco_cco_id == logged_user)
                .where(V2Engagement.dc_engagement_id == dc_engagement_id)
                .where(
                    V2MonitorContracts.contract_number == new_contract.contract_number
                )
            )
        )
        .scalars()
        .one_or_none()
    )

    if existing_contract is None:
        new_contract.dc_engagement_id = dc_engagement_id
        new_contract.created_by = logged_user
        new_contract.create_dtm = dt.datetime.now()
        for field, value in data.dict(exclude_unset=True).items():
            setattr(new_contract, field, value)
        new_contract.monitor_notes = data.monitor_notes
        session.add(new_contract)
        session.commit()
        session.refresh(new_contract)
        return new_contract
    elif existing_contract.is_deleted == "T":
        existing_contract.is_deleted = "F"
        existing_contract.updated_dtm = dt.datetime.now()
        existing_contract.updated_by = logged_user
        existing_contract.monitor_notes = data.monitor_notes
        existing_contract.monitor_type_id = data.monitor_type_id
        session.add(existing_contract)
        session.commit()
        session.refresh(existing_contract)
        return existing_contract
    else:
        raise HTTPException(status_code=409, detail="Contract number already exists")


@router.put(
    "/monitor/{dc_engagement_id}", response_model=None, status_code=HTTP_201_CREATED
)
def put_unmanaged_contracts_v2(
    data: V2MonitorContract_Update_Create,
    dc_engagement_id: int,
    req: UserRequest,
    session: GetSessionDep,
    logged_user: Optional[str] = None,
):
    logged_user = GET_logged_user(req, logged_user)

    user = session.exec(
        select(V2User)
        .join(V2CamEngagement)
        .where(V2User.cisco_cco_id == logged_user)
        .where(V2CamEngagement.dc_engagement_id == dc_engagement_id)
    ).one_or_none()
    if not user:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="You are not authorized to add contracts on this engagement",
        )

    existing_contract = (
        (
            session.execute(
                select(V2MonitorContracts)
                .join(V2Engagement)
                .join(V2CamEngagement)
                .join(V2User)
                .where(V2User.cisco_cco_id == logged_user)
                .where(V2Engagement.dc_engagement_id == dc_engagement_id)
                .where(V2MonitorContracts.contract_number == data.contract_number)
            )
        )
        .scalars()
        .one()
    )

    if existing_contract is None:
        raise HTTPException(status_code=409, detail="Contract does not exists")
    else:
        existing_contract.is_deleted = "F"
        existing_contract.updated_dtm = dt.datetime.now()
        existing_contract.updated_by = logged_user
        existing_contract.monitor_notes = data.monitor_notes  # notes really!
        existing_contract.monitor_type_id = data.monitor_type_id
        session.add(existing_contract)
        session.commit()
        session.refresh(existing_contract)
        return existing_contract


@router.delete(
    "/monitor/{dc_engagement_id}/{contract_number}",
    response_model=None,
    status_code=HTTP_200_OK,
)
def delete_unmanaged_contracts_v2(
    dc_engagement_id: int,
    contract_number: int,
    req: UserRequest,
    session: GetSessionDep,
    logged_user: Optional[str] = None,
):
    logged_user = GET_logged_user(req, logged_user)

    user = session.exec(
        select(V2User)
        .join(V2CamEngagement)
        .where(V2User.cisco_cco_id == logged_user)
        .where(V2CamEngagement.dc_engagement_id == dc_engagement_id)
    ).one_or_none()

    if not user:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="You are not authorized to add contracts on this engagement",
        )

    existing_contract = (
        (
            session.execute(
                select(V2MonitorContracts)
                .join(V2Engagement)
                .join(V2CamEngagement)
                .join(V2User)
                .where(V2User.cisco_cco_id == logged_user)
                .where(V2Engagement.dc_engagement_id == dc_engagement_id)
                .where(V2MonitorContracts.contract_number == contract_number)
            )
        )
        .scalars()
        .one()
    )
    #
    if existing_contract is None:
        raise HTTPException(status_code=409, detail="Contract does not exist")
    else:
        existing_contract.is_deleted = "T"
        existing_contract.updated_dtm = dt.datetime.now()
        existing_contract.updated_by = logged_user
        session.add(existing_contract)
        session.commit()
        session.refresh(existing_contract)
        return existing_contract


@router.get("/booking/{dc_engagement_id}")
def get_booking_contracts(
    dc_engagement_id: int,
    req: UserRequest,
    session: GetSessionDep,
    logged_user: Optional[str] = None,
) -> list[V2BookingContractRead]:
    logged_user = GET_logged_user(req, logged_user)
    user_engagements_query = query_users_engagements(logged_user).where(
        V2Engagement.dc_engagement_id == dc_engagement_id
    )

    user_engagement = session.exec(user_engagements_query).one_or_none()
    if not user_engagement:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND, detail="Engagement not found"
        )

    get_tags_query = query_engagement_booking_contracts(
        dc_engagement_id=dc_engagement_id,
        cisco_cco_id=logged_user,
        booking_contract=None,
    )
    tags = session.execute(get_tags_query).scalars().fetchall()
    res = []
    if not tags:
        return res
    for r in tags:
        res.append(json.loads(r))
    return res


@router.post(
    "/managed/{dc_engagement_id}", response_model=None, status_code=HTTP_201_CREATED
)
def net_managed_contracts_v2(
    data: V2BookingContract_POST,
    dc_engagement_id: int,
    req: UserRequest,
    session: GetSessionDep,
    logged_user: Optional[str] = None,
):
    logged_user = GET_logged_user(req, logged_user)

    logger.info(json.dumps(jsonable_encoder(data)))
    with session:
        load_query = text(
            """create or replace temporary table CPS_DSCI_STG.json_input as
                with i as (
                    select parse_json(:json) as json_data
                ), sub as (
                    select distinct json_data:booking_contract::number         as booking_contract,
                           json_data:dc_engagement_id::number         as dc_engagement_id,
                           cert.value:allowed_service_levels::varchar as allowed_service_levels,
                           cert.value:contract_number::varchar        as contract_number,
                           cert.value:user::varchar                  as user_cco_id,
                           cert.value:notes::varchar                  as notes,
                           cert.value:contract_name::varchar                  as name
                    from i , lateral flatten(input => i.json_data:managed_contracts) cert
                    )
                select sub.*, u.USER_ID from sub join DC_USERS u on (user_cco_id=u.CISCO_CCO_ID);
                """
        ).bindparams(
            bindparam("json", json.dumps(jsonable_encoder(data)), type_=String),
        )
        tags = session.execute(load_query)

        delete_query = text(
            """
                update DC_MANAGED_SERVICE_CONTRACTS c
                    set c.IS_DELETED = 'T' , c.UPDATED_BY = :logged_user, c.UPDATE_DTM = current_timestamp
                    from (
                        with curr as (
                            select  sc.*  from
                                DC_MANAGED_SERVICE_CONTRACTS sc join DC_USERS u on (u.cisco_cco_id =  :logged_user and sc.DC_USER_ID=u.USER_ID and u.IS_DELETED = 'F')
                                join DC_BOOKINGS_CONTRACTS_RESPONSIBLE_USERS  ru  on ( ru.BOOKING_CONTRACT=sc.BOOKING_CONTRACT and ru.DC_USER_ID=sc.DC_USER_ID)
                                join DC_ENGAGEMENT_TO_BOOKINGS_RESPONSIBLE_USER eru on (eru.BOOKING_CONTRACT=ru.BOOKING_CONTRACT and eru.DC_USER_ID=ru.DC_USER_ID )
                                where sc.DC_ENGAGEMENT_ID = :dc_engagement_id and ru.IS_DELETED = 'F' and eru.IS_DELETED = 'F' and sc.IS_DELETED = 'F'
                            )
                        select curr.* from curr left join CPS_DSCI_STG.json_input i on
                            (curr.DC_USER_ID = i.USER_ID and
                             curr.BOOKING_CONTRACT = i.booking_contract and
                             curr.DC_ENGAGEMENT_ID = i.dc_engagement_id and
                             curr.CONTRACT_NUMBER = i.contract_number
                                )
                        where i.contract_number is null and curr.BOOKING_CONTRACT = :edited_booking_contract
                    ) o
                    where   c.DC_USER_ID = o.DC_USER_ID and
                            c.BOOKING_CONTRACT = o.booking_contract and
                            c.DC_ENGAGEMENT_ID = o.dc_engagement_id and
                            c.CONTRACT_NUMBER = o.contract_number;
                    """
        ).bindparams(
            bindparam("logged_user", logged_user, type_=String),
            bindparam("dc_engagement_id", dc_engagement_id, type_=Integer),
            bindparam("edited_booking_contract", data.booking_contract, type_=Integer),
        )
        session.execute(delete_query)

        merge_query = text(
            """
            MERGE INTO DC_MANAGED_SERVICE_CONTRACTS c
                USING CPS_DSCI_STG.json_input AS b
                    ON      c.DC_USER_ID       = b.USER_ID
                        and c.dc_engagement_id = b.dc_engagement_id
                        and c.booking_contract = b.booking_contract
                        and c.contract_number  = b.contract_number
                    WHEN MATCHED THEN
                        UPDATE SET c.contract_name =b.name, c.allowed_service_levels=b.allowed_service_levels,
                            c.notes=b.notes, c.UPDATED_BY =b.user_cco_id, c.UPDATE_DTM=current_timestamp, c.IS_DELETED = 'F'
                    WHEN NOT MATCHED THEN
                        INSERT(   dc_user_id,   booking_contract,   contract_number,  dc_engagement_id,
                               allowed_service_levels,    notes, contract_name,  CREATE_DTM, CREATED_BY)
                          VALUES (b.USER_ID,  b.booking_contract, b.contract_number,b.dc_engagement_id,
                             b.allowed_service_levels, b.notes, b.name,      current_timestamp, b.user_cco_id);
                """
        )
        session.execute(merge_query).scalars().all()
        booking_contract = data.booking_contract if data.booking_contract > 0 else None
        get_tags_query = query_engagement_booking_contracts(
            dc_engagement_id, logged_user, booking_contract
        )
        tags = session.execute(get_tags_query).scalars().all()

        logger.info(tags)
        session.commit()

        res = []
        if not tags:
            return res
        for r in tags:
            res.append(json.loads(r))
        return res


###################################################################################
####Below here are functions not exposed to routes#################################
###################################################################################


@router.get("/linkable/")
def linkable_contracts_v2(
    req: UserRequest,
    session: GetSessionDep,
    logged_user: Optional[str] = None,
):
    """Get the tagsets and related tags for an engagement"""
    logged_user = GET_logged_user(req, logged_user)

    get_query = text(
        """with sub as (
            select  distinct case when claim.BOOKING_CONTRACT is null then 'T' else 'F' end as is_linkable,
                   u.USER_ID, ru.BOOKING_CONTRACT, rl.BOOKINGS_ROLE, c.ACCOUNT_NAME, 
                   pm.PRICING_MODEL_NAME, st.SOLD_AS_SERVICE_NAME,bp.BUYING_PROGRAM_NAME,claim.dc_engagement_id
            from  dc_users u
                join dc_BOOKINGS_CONTRACTS_RESPONSIBLE_USERS ru on ( ru.DC_USER_ID=u.user_id )
                join dc_BOOKINGS_CONTRACTS c on ( c.BOOKING_CONTRACT=ru.BOOKING_CONTRACT)
                join dc_bookings_user_role rl on ( rl.bookings_role_id=ru.SERVICE_ROLE_ID)
                join dc_pricing_model pm on (pm.PRICING_type_id  = c.SOLD_AS_PRICING_TYPE_ID )
                join dc_sold_as_service_types st on (c.SOLD_AS_SERVICE_TYPE_ID = st.service_type_id )
                join dc_buying_programs bp on ( bp.BUYING_PROGRAM_TYPE_ID= c.BUYING_PROGRAM_TYPE_ID)
                left join dc_ENGAGEMENT_TO_BOOKINGS_RESPONSIBLE_USER claim on
                    ( claim.BOOKING_CONTRACT=ru.BOOKING_CONTRACT
                        and
                      claim.DC_USER_ID  = ru.DC_USER_ID
                        and
                      claim.IS_DELETED = 'F'
                    )
                where u.is_deleted = 'F' and ru.IS_DELETED = 'F' and c.IS_DELETED = 'F' and u.cisco_cco_id = :user_cco 
                )
                select TO_JSON(OBJECT_CONSTRUCT_KEEP_NULL(
                       'is_linkable',           sub.is_linkable,
                       'user_id',               sub.USER_ID,
                       'booking_contract',      sub.BOOKING_CONTRACT,
                       'bookings_role',         sub.BOOKINGS_ROLE,
                       'account_name',          sub.ACCOUNT_NAME,
                       'pricing_model',         sub.PRICING_MODEL_NAME,
                       'service_name',          sub.SOLD_AS_SERVICE_NAME,
                       'buying_program_name' ,  sub.BUYING_PROGRAM_NAME,
                       'dc_engagement_id' ,     e.dc_engagement_id,
                       'engagement_name' ,      e.engagement_name
                   )) from sub left join dc_engagement_hdr e on (e.dc_engagement_id = sub.dc_engagement_id )
      """
    ).bindparams(
        bindparam("user_cco", logged_user, type_=String),
    )
    tags = session.execute(get_query).scalars().fetchall()
    res = []
    if not tags:
        return res

    for r in tags:
        res.append(json.loads(r))
    return res
