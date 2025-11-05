import json
import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from snowflake.sqlalchemy import MergeInto
from sqlalchemy import and_, literal, literal_column, update
from sqlmodel import select
from starlette.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

from api.dependencies import GetSessionDep, GetUserDep
from api.v2.models import (
    AdminSDPDeliverable as SDPDeliverableModel,
)
from api.v2.models import (
    AdminSDPDeliverableCreate,
    AdminSDPDeliverableEdit,
)
from api.v2.orm.admin import SDPDeliverable, SDPTask, SDPTaskToDeliverable
from api.v2.queries import query_admin_sdp_deliverable_detail
from api.v2.queries.parse_json_into_table import parse_json_into_table, using_source
from api.v2.queries.utils import MergeTargetRelations, QueryMembership

router = APIRouter()
logger = logging.getLogger("api")


@router.get("/{deliverable_id}", response_model=SDPDeliverableModel)
def get_sdp_deliverable(deliverable_id: int, session: GetSessionDep):
    """Get a SDPDeliverable by ID"""
    query = query_admin_sdp_deliverable_detail(deliverable_id)
    db_deliverable = session.exec(query).one()
    return db_deliverable


@router.post("", response_model=SDPDeliverableModel)
def create_sdp_deliverable(
    payload: AdminSDPDeliverableCreate, session: GetSessionDep, db_user: GetUserDep
):
    query_members = (
        QueryMembership().add_orm_membership(SDPTask, payload.task_ids).build()
    )

    non_existent_task_ids = session.exec(query_members).all()
    if non_existent_task_ids:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"Task IDs {non_existent_task_ids} do not exist",
        )

    db_deliverable = SDPDeliverable.create_from_model(
        payload, db_user.cisco_cco_id, session
    )

    created_by = updated_by = db_user.cisco_cco_id
    create_dtm = update_dtm = datetime.now()

    # Deliverable / Task
    source_values = [
        {"deliverable_id": db_deliverable.deliverable_id, "task_id": task_id}
        for task_id in payload.task_ids
    ]

    fn = parse_json_into_table(json.dumps(source_values, separators=(",", ":")))

    # noinspection PyTypeChecker,PydanticTypeChecker
    source_virtual = (
        select(
            literal_column("value:deliverable_id::INTEGER").label("deliverable_id"),
            literal_column("value:task_id::INTEGER").label("task_id"),
        )
        .select_from(fn)
        .cte("source_virtual")
    )

    merge_tasks = MergeInto(
        target=SDPTaskToDeliverable.__table__,
        source=using_source(source_virtual),
        on=and_(
            SDPTaskToDeliverable.deliverable_id == source_virtual.c.deliverable_id,
            SDPTaskToDeliverable.task_id == source_virtual.c.task_id,
        ),
    )
    merge_tasks.when_matched_then_update().where(
        SDPTaskToDeliverable.is_deleted == "T"
    ).values(
        is_deleted=literal("F"),
        updated_by=literal(updated_by),
        update_dtm=literal(update_dtm),
    )
    merge_tasks.when_not_matched_then_insert().values(
        deliverable_id=source_virtual.c.deliverable_id,
        task_id=source_virtual.c.task_id,
        created_by=literal(created_by),
        create_dtm=literal(create_dtm),
        is_deleted=literal("F"),
    )
    session.exec(merge_tasks)
    session.commit()

    return session.exec(
        query_admin_sdp_deliverable_detail(db_deliverable.deliverable_id)
    ).one()


@router.patch("/{deliverable_id}", response_model=SDPDeliverableModel)
def edit_sdp_deliverable(
    payload: AdminSDPDeliverableEdit,
    db_user: GetUserDep,
    session: GetSessionDep,
    deliverable_id: int,
):
    """Edit a SDPDeliverable."""

    if payload.deliverable_id != deliverable_id:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST, detail="Path ID does not match payload ID"
        )

    query_members = (
        QueryMembership().add_orm_membership(SDPTask, payload.task_ids).build()
    )

    non_existent_task_ids = session.exec(query_members).all()
    if non_existent_task_ids:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"Task IDs {non_existent_task_ids} do not exist",
        )

    db_deliverable = session.exec(
        select(SDPDeliverable)
        .where(SDPDeliverable.deliverable_id == deliverable_id)
        .where(SDPDeliverable.is_deleted == "F")
    ).one()

    db_deliverable.update_from_model(payload, db_user.cisco_cco_id, session)

    created_by = updated_by = db_user.cisco_cco_id
    create_dtm = update_dtm = datetime.now()

    task_merger = MergeTargetRelations(
        target=SDPDeliverable,
        target_id_col=SDPDeliverable.deliverable_id,
        secondary=SDPTaskToDeliverable,
        secondary_target_col=SDPTaskToDeliverable.deliverable_id,
        secondary_rel_col=SDPTaskToDeliverable.task_id,
        related=SDPTask,
        related_id_col=SDPTask.task_id,
    )

    existing_task_ids = session.exec(
        task_merger.build_existing_query(db_deliverable.deliverable_id)
    )

    task_virtual_source = task_merger.build_virtual_source(
        target_id=db_deliverable.deliverable_id,
        proposed=payload.task_ids,
        existing=existing_task_ids,
    )

    merge_task = MergeInto(
        target=SDPTaskToDeliverable.__table__,
        source=using_source(task_virtual_source),
        on=and_(
            SDPTaskToDeliverable.deliverable_id == task_virtual_source.c.deliverable_id,
            SDPTaskToDeliverable.task_id == task_virtual_source.c.task_id,
        ),
    )

    merge_task.when_matched_then_update().where(
        and_(
            SDPTaskToDeliverable.is_deleted == "T",
            task_virtual_source.c.is_deleted == "F",
        )
    ).values(
        is_deleted=literal("F"),
        updated_by=literal(updated_by),
        update_dtm=literal(update_dtm),
    )

    merge_task.when_matched_then_update().where(
        and_(
            SDPTaskToDeliverable.is_deleted == "F",
            task_virtual_source.c.is_deleted == "T",
        )
    ).values(
        is_deleted=literal("T"),
        updated_by=literal(updated_by),
        update_dtm=literal(update_dtm),
    )

    merge_task.when_not_matched_then_insert().values(
        deliverable_id=task_virtual_source.c.deliverable_id,
        task_id=task_virtual_source.c.task_id,
        created_by=literal(created_by),
        create_dtm=literal(create_dtm),
        is_deleted=literal("F"),
    )

    session.exec(merge_task)
    session.commit()

    return session.exec(
        query_admin_sdp_deliverable_detail(db_deliverable.deliverable_id)
    ).one()


@router.delete("/{deliverable_id}")
def delete_sdp_deliverable(
    deliverable_id: int, session: GetSessionDep, db_user: GetUserDep
) -> JSONResponse:
    """Delete a SDPDeliverable by ID"""
    db_deliverable = session.exec(
        select(SDPDeliverable)
        .where(SDPDeliverable.deliverable_id == deliverable_id)
        .where(SDPDeliverable.is_deleted == "F")
    ).one()

    db_deliverable.soft_delete(db_user.cisco_cco_id, session)

    # Cascade soft delete to task relations
    update_tasks = (
        update(SDPTaskToDeliverable)
        .where(SDPTaskToDeliverable.deliverable_id == deliverable_id)
        .where(SDPTaskToDeliverable.is_deleted == "F")
        .values(
            is_deleted="T", updated_by=db_user.cisco_cco_id, update_dtm=datetime.now()
        )
    )

    session.exec(update_tasks)
    session.commit()

    return JSONResponse(
        status_code=HTTP_200_OK,
        content={"success": True, "message": "Deliverable deleted successfully"},
    )
