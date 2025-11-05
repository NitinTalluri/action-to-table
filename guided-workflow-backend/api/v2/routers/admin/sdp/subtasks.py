import json
import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException
from snowflake.sqlalchemy import MergeInto
from sqlalchemy import DateTime, and_, literal, literal_column, update
from sqlmodel import select
from starlette.responses import JSONResponse
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND, HTTP_409_CONFLICT

from api.dependencies import GetSessionDep, GetUserDep
from api.v2.models import (
    AdminSDPSubTask as SDPSubTaskModel,
)
from api.v2.models import (
    AdminSDPSubTaskCreate,
    AdminSDPSubTaskEdit,
)
from api.v2.orm import (
    V2BuyingPrograms,
    V2PricingModel,
    V2ServicePlans,
)
from api.v2.orm.admin import (
    SDPSubTask,
    SDPSubTaskBuyingPrograms,
    SDPSubTaskPricingModels,
    SDPSubTaskServicePlans,
    SDPTask,
    SDPTaskToSubTask,
)
from api.v2.queries import QueryMembership, query_admin_sdp_subtask
from api.v2.queries.parse_json_into_table import parse_json_into_table, using_source
from api.v2.queries.utils import MergeTargetRelations

logger = logging.getLogger("api")
router = APIRouter()


@router.get("/{sub_task_id}", response_model=SDPSubTaskModel)
def get_sdp_subtask(sub_task_id: int, session: GetSessionDep):
    """Get a SDP Subtask's Details and Enablements"""
    query = query_admin_sdp_subtask(sub_task_id)
    result = session.exec(query).one()

    return result


@router.post("", response_model=SDPSubTaskModel)
def create_sdp_subtask(
    payload: AdminSDPSubTaskCreate, db_user: GetUserDep, session: GetSessionDep
):
    """Create a new SDP Subtask"""

    query_members = (
        QueryMembership()
        .add_orm_membership(V2ServicePlans, payload.sold_as_service_type_ids)
        .add_orm_membership(V2PricingModel, payload.pricing_type_ids)
        .add_orm_membership(V2BuyingPrograms, payload.buying_program_type_ids)
        .add_orm_membership(SDPTask, payload.task_ids)
    )

    non_existing_ids = session.exec(query_members.build()).all()
    if non_existing_ids:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="One or more of the provided IDs do not exist",
        )

    db_sub_task = SDPSubTask.create_from_model(payload, db_user.cisco_cco_id, session)

    lit_dt = literal(datetime.now())
    lit_user = literal(db_user.cisco_cco_id)

    # task/subtask

    source_values = [
        {
            "task_id": task_id,
            "sub_task_id": db_sub_task.sub_task_id,
        }
        for task_id in payload.task_ids
    ]

    fn = parse_json_into_table(json.dumps(source_values, separators=(",", ":")))

    # noinspection PyTypeChecker,PydanticTypeChecker
    source_virtual = (
        select(
            literal_column("value:task_id::INTEGER").label("task_id"),
            literal_column("value:sub_task_id::INTEGER").label("sub_task_id"),
        )
        .select_from(fn)
        .cte("source_virtual")
    )

    merge_tasks = MergeInto(
        target=SDPTaskToSubTask.__table__,
        source=using_source(source_virtual),
        on=and_(
            SDPTaskToSubTask.task_id == source_virtual.c.task_id,
            SDPTaskToSubTask.sub_task_id == source_virtual.c.sub_task_id,
        ),
    )
    merge_tasks.when_matched_then_update().where(
        SDPTaskToSubTask.is_deleted == "T"
    ).values(is_deleted=literal("F"), updated_by=lit_user, update_dtm=lit_dt)
    merge_tasks.when_not_matched_then_insert().values(
        task_id=source_virtual.c.task_id,
        sub_task_id=source_virtual.c.sub_task_id,
        is_deleted=literal("F"),
        created_by=lit_user,
        create_dtm=lit_dt,
    )
    session.exec(merge_tasks)
    session.commit()

    # subtask/buying_program

    source_values = [
        {
            "sub_task_id": db_sub_task.sub_task_id,
            "buying_program_type_id": buying_program_type_id,
        }
        for buying_program_type_id in payload.buying_program_type_ids
    ]

    fn = parse_json_into_table(json.dumps(source_values, separators=(",", ":")))

    # noinspection PyTypeChecker,PydanticTypeChecker

    source_virtual = (
        select(
            literal_column("value:sub_task_id::INTEGER").label("sub_task_id"),
            literal_column("value:buying_program_type_id::INTEGER").label(
                "buying_program_type_id"
            ),
        )
        .select_from(fn)
        .cte("source_virtual")
    )

    merge_buying_programs = MergeInto(
        target=SDPSubTaskBuyingPrograms.__table__,
        source=using_source(source_virtual),
        on=and_(
            SDPSubTaskBuyingPrograms.sub_task_id == source_virtual.c.sub_task_id,
            SDPSubTaskBuyingPrograms.buying_program_type_id
            == source_virtual.c.buying_program_type_id,
        ),
    )

    merge_buying_programs.when_matched_then_update().where(
        SDPSubTaskBuyingPrograms.is_deleted == "T"
    ).values(is_deleted=literal("F"), updated_by=lit_user, update_dtm=lit_dt)
    merge_buying_programs.when_not_matched_then_insert().values(
        sub_task_id=source_virtual.c.sub_task_id,
        buying_program_id=source_virtual.c.buying_program_type_id,
        is_deleted=literal("F"),
        created_by=lit_user,
        create_dtm=lit_dt,
    )
    session.exec(merge_buying_programs)
    session.commit()

    # subtask/pricing_model

    source_values = [
        {
            "sub_task_id": db_sub_task.sub_task_id,
            "pricing_type_id": pricing_type_id,
        }
        for pricing_type_id in payload.pricing_type_ids
    ]

    fn = parse_json_into_table(json.dumps(source_values, separators=(",", ":")))

    # noinspection PyTypeChecker,PydanticTypeChecker
    source_virtual = (
        select(
            literal_column("value:sub_task_id::INTEGER").label("sub_task_id"),
            literal_column("value:pricing_type_id::INTEGER").label("pricing_type_id"),
        )
        .select_from(fn)
        .cte("source_virtual")
    )

    merge_pricing_model = MergeInto(
        target=SDPSubTaskPricingModels.__table__,
        source=using_source(source_virtual),
        on=and_(
            SDPSubTaskPricingModels.sub_task_id == source_virtual.c.sub_task_id,
            SDPSubTaskPricingModels.pricing_type_id == source_virtual.c.pricing_type_id,
        ),
    )
    merge_pricing_model.when_matched_then_update().where(
        SDPSubTaskPricingModels.is_deleted == "T"
    ).values(is_deleted=literal("F"), updated_by=lit_user, update_dtm=lit_dt)
    merge_pricing_model.when_not_matched_then_insert().values(
        sub_task_id=source_virtual.c.sub_task_id,
        pricing_model_id=source_virtual.c.pricing_type_id,
        is_deleted=literal("F"),
        created_by=lit_user,
        create_dtm=lit_dt,
    )

    session.exec(merge_pricing_model)
    session.commit()

    # subtask/sold_as_service_type

    source_values = [
        {
            "sub_task_id": db_sub_task.sub_task_id,
            "service_type_id": service_type_id,
        }
        for service_type_id in payload.sold_as_service_type_ids
    ]

    fn = parse_json_into_table(json.dumps(source_values, separators=(",", ":")))

    # noinspection PyTypeChecker,PydanticTypeChecker
    source_virtual = (
        select(
            literal_column("value:sub_task_id::INTEGER").label("sub_task_id"),
            literal_column("value:service_type_id::INTEGER").label("service_type_id"),
        )
        .select_from(fn)
        .cte("source_virtual")
    )

    merge_service_types = MergeInto(
        target=SDPSubTaskServicePlans.__table__,
        source=using_source(source_virtual),
        on=and_(
            SDPSubTaskServicePlans.sub_task_id == source_virtual.c.sub_task_id,
            SDPSubTaskServicePlans.sold_as_service_type_id
            == source_virtual.c.service_type_id,
        ),
    )

    merge_service_types.when_matched_then_update().where(
        SDPSubTaskServicePlans.is_deleted == "T"
    ).values(is_deleted=literal("F"), updated_by=lit_user, update_dtm=lit_dt)

    merge_service_types.when_not_matched_then_insert().values(
        sub_task_id=source_virtual.c.sub_task_id,
        sold_as_service_id=source_virtual.c.service_type_id,
        is_deleted=literal("F"),
        created_by=lit_user,
        create_dtm=lit_dt,
    )

    session.exec(merge_service_types)
    session.commit()

    return session.exec(query_admin_sdp_subtask(db_sub_task.sub_task_id)).one()


@router.patch("/{sub_task_id}", response_model=SDPSubTaskModel)
def edit_sdp_subtask(
    payload: AdminSDPSubTaskEdit,
    db_user: GetUserDep,
    session: GetSessionDep,
    sub_task_id: int,
):
    """Edit a SDP Subtask."""

    if sub_task_id != payload.sub_task_id:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=f"Path ID [{sub_task_id}] does not match payload ID [{payload.sub_task_id}]",
        )

    db_sub_task = session.exec(
        select(SDPSubTask)
        .where(SDPSubTask.sub_task_id == sub_task_id)
        .where(SDPSubTask.is_deleted == "F")
    ).one()

    db_sub_task.update_from_model(payload, db_user.cisco_cco_id, session)

    # We check for four relations, task_ids, sold_as_service_type_ids, pricing_type_ids, buying_program_type_ids

    query_members = (
        QueryMembership()
        .add_orm_membership(V2ServicePlans, payload.sold_as_service_type_ids)
        .add_orm_membership(V2PricingModel, payload.pricing_type_ids)
        .add_orm_membership(V2BuyingPrograms, payload.buying_program_type_ids)
        .add_orm_membership(SDPTask, payload.task_ids)
        .build()
    )

    existing_ids = session.exec(query_members).all()

    if existing_ids:
        logger.error("Non-existing IDs found: %s", existing_ids)
        raise HTTPException(
            status_code=HTTP_409_CONFLICT,
            detail="One or more of the provided IDs do not exist",
        )

    # Building mergers and queries

    task_merger = MergeTargetRelations(
        target=SDPSubTask,
        target_id_col=SDPSubTask.sub_task_id,
        secondary=SDPTaskToSubTask,
        secondary_target_col=SDPTaskToSubTask.sub_task_id,
        secondary_rel_col=SDPTaskToSubTask.task_id,
        related=SDPTask,
        related_id_col=SDPTask.task_id,
    )

    buying_program_merger = MergeTargetRelations(
        target=SDPSubTask,
        target_id_col=SDPSubTask.sub_task_id,
        secondary=SDPSubTaskBuyingPrograms,
        secondary_target_col=SDPSubTaskBuyingPrograms.sub_task_id,
        secondary_rel_col=SDPSubTaskBuyingPrograms.buying_program_type_id,
        related=V2BuyingPrograms,
        related_id_col=V2BuyingPrograms.buying_program_type_id,
    )
    pricing_model_merger = MergeTargetRelations(
        target=SDPSubTask,
        target_id_col=SDPSubTask.sub_task_id,
        secondary=SDPSubTaskPricingModels,
        secondary_target_col=SDPSubTaskPricingModels.sub_task_id,
        secondary_rel_col=SDPSubTaskPricingModels.pricing_type_id,
        related=V2PricingModel,
        related_id_col=V2PricingModel.pricing_type_id,
    )

    service_type_merger = MergeTargetRelations(
        target=SDPSubTask,
        target_id_col=SDPSubTask.sub_task_id,
        secondary=SDPSubTaskServicePlans,
        secondary_target_col=SDPSubTaskServicePlans.sub_task_id,
        secondary_rel_col=SDPSubTaskServicePlans.sold_as_service_type_id,
        related=V2ServicePlans,
        related_id_col=V2ServicePlans.service_type_id,
    )

    existing_service_types_query = service_type_merger.build_existing_query(sub_task_id)
    existing_pricing_models_query = pricing_model_merger.build_existing_query(
        sub_task_id
    )
    existing_tasks_query = task_merger.build_existing_query(sub_task_id)
    existing_buying_programs_query = buying_program_merger.build_existing_query(
        sub_task_id
    )

    existing_tasks = session.exec(existing_tasks_query).all()
    existing_buying_programs = session.exec(existing_buying_programs_query).all()
    existing_pricing_models = session.exec(existing_pricing_models_query).all()
    existing_service_types = session.exec(existing_service_types_query).all()

    task_virtual_source = task_merger.build_virtual_source(
        target_id=sub_task_id, proposed=payload.task_ids, existing=existing_tasks
    )

    lit_dt = literal(datetime.now(), type_=DateTime)
    lit_user = literal(db_user.cisco_cco_id)

    merge_tasks = MergeInto(
        target=SDPTaskToSubTask.__table__,
        source=using_source(task_virtual_source),
        on=and_(
            SDPTaskToSubTask.sub_task_id == task_virtual_source.c.sub_task_id,
            SDPTaskToSubTask.task_id == task_virtual_source.c.task_id,
        ),
    )

    merge_tasks.when_matched_then_update().where(
        and_(
            SDPTaskToSubTask.is_deleted == "T", task_virtual_source.c.is_deleted == "F"
        )
    ).values(is_deleted=literal("F"), updated_by=lit_user, update_dtm=lit_dt)
    merge_tasks.when_matched_then_update().where(
        and_(
            SDPTaskToSubTask.is_deleted == "F", task_virtual_source.c.is_deleted == "T"
        )
    ).values(is_deleted=literal("T"), updated_by=lit_user, update_dtm=lit_dt)
    merge_tasks.when_not_matched_then_insert().values(
        task_id=task_virtual_source.c.task_id,
        sub_task_id=task_virtual_source.c.sub_task_id,
        is_deleted=task_virtual_source.c.is_deleted,
        create_dtm=lit_dt,
        created_by=lit_user,
    )

    # Subtask/Buying Program

    buying_program_virtual_source = buying_program_merger.build_virtual_source(
        target_id=sub_task_id,
        proposed=payload.buying_program_type_ids,
        existing=existing_buying_programs,
    )

    merge_buying_programs = MergeInto(
        target=SDPSubTaskBuyingPrograms.__table__,
        source=using_source(buying_program_virtual_source),
        on=and_(
            SDPSubTaskBuyingPrograms.sub_task_id
            == buying_program_virtual_source.c.sub_task_id,
            SDPSubTaskBuyingPrograms.buying_program_type_id
            == buying_program_virtual_source.c.buying_program_type_id,
        ),
    )

    merge_buying_programs.when_matched_then_update().where(
        and_(
            SDPSubTaskBuyingPrograms.is_deleted == "T",
            buying_program_virtual_source.c.is_deleted == "F",
        )
    ).values(is_deleted=literal("F"), updated_by=lit_user, update_dtm=lit_dt)

    merge_buying_programs.when_matched_then_update().where(
        and_(
            SDPSubTaskBuyingPrograms.is_deleted == "F",
            buying_program_virtual_source.c.is_deleted == "T",
        )
    ).values(is_deleted=literal("T"), updated_by=lit_user, update_dtm=lit_dt)

    merge_buying_programs.when_not_matched_then_insert().values(
        sub_task_id=buying_program_virtual_source.c.sub_task_id,
        buying_program_id=buying_program_virtual_source.c.buying_program_type_id,
        is_deleted=buying_program_virtual_source.c.is_deleted,
        created_by=lit_user,
        create_dtm=lit_dt,
    )

    # Subtask/Pricing Model

    pricing_model_virtual_source = pricing_model_merger.build_virtual_source(
        target_id=sub_task_id,
        proposed=payload.pricing_type_ids,
        existing=existing_pricing_models,
    )

    merge_pricing_models = MergeInto(
        target=SDPSubTaskPricingModels.__table__,
        source=using_source(pricing_model_virtual_source),
        on=and_(
            SDPSubTaskPricingModels.sub_task_id
            == pricing_model_virtual_source.c.sub_task_id,
            SDPSubTaskPricingModels.pricing_type_id
            == pricing_model_virtual_source.c.pricing_type_id,
        ),
    )

    merge_pricing_models.when_matched_then_update().where(
        and_(
            SDPSubTaskPricingModels.is_deleted == "T",
            pricing_model_virtual_source.c.is_deleted == "F",
        )
    ).values(is_deleted=literal("F"), updated_by=lit_user, update_dtm=lit_dt)

    merge_pricing_models.when_matched_then_update().where(
        and_(
            SDPSubTaskPricingModels.is_deleted == "F",
            pricing_model_virtual_source.c.is_deleted == "T",
        )
    ).values(is_deleted=literal("T"), updated_by=lit_user, update_dtm=lit_dt)

    merge_pricing_models.when_not_matched_then_insert().values(
        sub_task_id=pricing_model_virtual_source.c.sub_task_id,
        pricing_model_id=pricing_model_virtual_source.c.pricing_type_id,
        is_deleted=pricing_model_virtual_source.c.is_deleted,
        created_by=lit_user,
        create_dtm=lit_dt,
    )

    # Subtask/Sold As Service Type

    service_type_virtual_source = service_type_merger.build_virtual_source(
        target_id=sub_task_id,
        proposed=payload.sold_as_service_type_ids,
        existing=existing_service_types,
    )

    merge_service_types = MergeInto(
        target=SDPSubTaskServicePlans.__table__,
        source=using_source(service_type_virtual_source),
        on=and_(
            SDPSubTaskServicePlans.sub_task_id
            == service_type_virtual_source.c.sub_task_id,
            SDPSubTaskServicePlans.sold_as_service_type_id
            == service_type_virtual_source.c.sold_as_service_type_id,
        ),
    )

    merge_service_types.when_matched_then_update().where(
        and_(
            SDPSubTaskServicePlans.is_deleted == "T",
            service_type_virtual_source.c.is_deleted == "F",
        )
    ).values(is_deleted=literal("F"), updated_by=lit_user, update_dtm=lit_dt)

    merge_service_types.when_matched_then_update().where(
        and_(
            SDPSubTaskServicePlans.is_deleted == "F",
            service_type_virtual_source.c.is_deleted == "T",
        )
    ).values(is_deleted=literal("T"), updated_by=lit_user, update_dtm=lit_dt)

    merge_service_types.when_not_matched_then_insert().values(
        sub_task_id=service_type_virtual_source.c.sub_task_id,
        sold_as_service_id=service_type_virtual_source.c.sold_as_service_type_id,
        is_deleted=service_type_virtual_source.c.is_deleted,
        created_by=lit_user,
        create_dtm=lit_dt,
    )

    session.exec(merge_tasks)
    session.exec(merge_buying_programs)
    session.exec(merge_pricing_models)
    session.exec(merge_service_types)
    session.commit()

    return session.exec(query_admin_sdp_subtask(sub_task_id)).one()


@router.delete("/{sub_task_id}")
def delete_sdp_subtask(
    db_user: GetUserDep, session: GetSessionDep, sub_task_id: int
) -> JSONResponse:
    """Delete a SDP Subtask"""

    db_sub_task = session.exec(
        select(SDPSubTask)
        .where(SDPSubTask.sub_task_id == sub_task_id)
        .where(SDPSubTask.is_deleted == "F")
    ).one()

    db_sub_task.soft_delete(db_user.cisco_cco_id, session)

    dt_now = datetime.now()
    user = db_user.cisco_cco_id

    # Cascade deletes
    update_tasks = (
        update(SDPTaskToSubTask)
        .where(
            and_(
                SDPTaskToSubTask.sub_task_id == sub_task_id,
                SDPTaskToSubTask.is_deleted == "F",
            )
        )
        .values(is_deleted="T", updated_by=user, update_dtm=dt_now)
    )

    update_buying_programs = (
        update(SDPSubTaskBuyingPrograms)
        .where(
            and_(
                SDPSubTaskBuyingPrograms.sub_task_id == sub_task_id,
                SDPSubTaskBuyingPrograms.is_deleted == "F",
            )
        )
        .values(is_deleted="T", updated_by=user, update_dtm=dt_now)
    )

    update_pricing_models = (
        update(SDPSubTaskPricingModels)
        .where(
            and_(
                SDPSubTaskPricingModels.sub_task_id == sub_task_id,
                SDPSubTaskPricingModels.is_deleted == "F",
            )
        )
        .values(is_deleted="T", updated_by=user, update_dtm=dt_now)
    )

    session.exec(update_tasks)
    session.exec(update_buying_programs)
    session.exec(update_pricing_models)
    session.commit()

    return JSONResponse(
        content={"message": "Subtask deleted successfully"}, status_code=200
    )
