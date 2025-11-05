import json
import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, Response
from snowflake.sqlalchemy import MergeInto
from sqlalchemy import and_, literal, literal_column, update
from sqlmodel import select
from starlette.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

from api.dependencies import GetSessionDep, GetUserDep
from api.v2.models import AdminSDPTask, AdminSDPTaskCreate, AdminSDPTaskEdit
from api.v2.orm.admin import (
    SDPAnchorDate,
    SDPAnchorDateIterator,
    SDPDeliverable,
    SDPSubTask,
    SDPTask,
    SDPTaskToDeliverable,
    SDPTaskToSubTask,
)
from api.v2.queries import query_admin_sdp_task
from api.v2.queries.parse_json_into_table import parse_json_into_table, using_source
from api.v2.queries.utils import MergeTargetRelations, QueryMembership

logger = logging.getLogger("api")
router = APIRouter()


@router.get("/{task_id}", response_model=AdminSDPTask)
def get_sdp_task(task_id: int, session: GetSessionDep):
    """Get a SDP Task by ID"""
    db_task = session.exec(query_admin_sdp_task(task_id)).one_or_none()

    if not db_task:
        raise HTTPException(status_code=404, detail=f"Task with ID {task_id} not found")

    return db_task


@router.post("", response_model=AdminSDPTask)
def create_sdp_task(
    payload: AdminSDPTaskCreate,
    db_user: GetUserDep,
    session: GetSessionDep,
):
    """Create a new SDPTask."""
    # We check for two relations, sub_task_id, and deliverable_id

    query_members = (
        QueryMembership()
        .add_orm_membership(SDPSubTask, payload.sub_task_ids)
        .add_orm_membership(SDPDeliverable, payload.deliverable_ids)
        .add_orm_membership(SDPAnchorDate, [payload.anchor_date_id])
        .add_orm_membership(SDPAnchorDateIterator, [payload.cycle_iterator_id])
        .build()
    )

    non_existent_members = session.exec(query_members).all()
    if non_existent_members:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND, detail="One or more related ids not found"
        )

    db_sdp_task = SDPTask.create_from_model(payload, db_user.cisco_cco_id, session)

    lit_dt = literal(datetime.now())
    lit_user = literal(db_user.cisco_cco_id)

    # Merging task/subtask relationships

    source_st_values = [
        {"task_id": db_sdp_task.task_id, "sub_task_id": sub_task_id}
        for sub_task_id in payload.sub_task_ids
    ]

    fn = parse_json_into_table(json.dumps(source_st_values, separators=(",", ":")))

    # noinspection PyTypeChecker,PydanticTypeChecker
    source_st = (
        select(
            literal_column("value:task_id::INTEGER").label("task_id"),
            literal_column("value:sub_task_id::INTEGER").label("sub_task_id"),
        )
        .select_from(fn)
        .alias("source_st")
    )
    merge_st = MergeInto(
        target=SDPTaskToSubTask.__table__,
        source=source_st,
        on=and_(
            SDPTaskToSubTask.task_id == source_st.c.task_id,
            SDPTaskToSubTask.sub_task_id == source_st.c.sub_task_id,
        ),
    )

    merge_st.when_matched_then_update().where(
        SDPTaskToSubTask.is_deleted == "T"
    ).values(is_deleted=literal("F"), update_dtm=lit_dt, updated_by=lit_user)
    merge_st.when_not_matched_then_insert().values(
        task_id=source_st.c.task_id,
        sub_task_id=source_st.c.sub_task_id,
        create_dtm=lit_dt,
        created_by=lit_user,
        is_deleted=literal("F"),
    )

    session.exec(merge_st)
    session.commit()

    source_deliverable_values = [
        {"task_id": db_sdp_task.task_id, "deliverable_id": deliverable_id}
        for deliverable_id in payload.deliverable_ids
    ]

    fn = parse_json_into_table(
        json.dumps(source_deliverable_values, separators=(",", ":"))
    )

    # noinspection PyTypeChecker,PydanticTypeChecker
    source_deliverable = (
        select(
            literal_column("value:task_id::INTEGER").label("task_id"),
            literal_column("value:deliverable_id::INTEGER").label("deliverable_id"),
        )
        .select_from(fn)
        .alias("source_deliverable")
    )
    merge_deliverable = MergeInto(
        target=SDPTaskToDeliverable.__table__,
        source=source_deliverable,
        on=and_(
            SDPTaskToDeliverable.task_id == source_deliverable.c.task_id,
            SDPTaskToDeliverable.deliverable_id == source_deliverable.c.deliverable_id,
        ),
    )

    merge_deliverable.when_matched_then_update().where(
        SDPTaskToDeliverable.is_deleted == "T"
    ).values(is_deleted=literal("F"), update_dtm=lit_dt, updated_by=lit_user)
    merge_deliverable.when_not_matched_then_insert().values(
        task_id=source_deliverable.c.task_id,
        deliverable_id=source_deliverable.c.deliverable_id,
        create_dtm=lit_dt,
        created_by=lit_user,
        is_deleted=literal("F"),
    )

    session.exec(merge_deliverable)
    session.commit()

    sdp_task_query = query_admin_sdp_task(db_sdp_task.task_id)
    db_sdp_task = session.exec(sdp_task_query).one()
    return db_sdp_task


@router.patch("/{task_id}", response_model=AdminSDPTask)
def edit_sdp_task(
    payload: AdminSDPTaskEdit, db_user: GetUserDep, session: GetSessionDep, task_id: int
):
    """Edit a SDPTask."""

    if task_id != payload.task_id:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Task ID mismatch")

    db_task = session.exec(
        select(SDPTask)
        .where(SDPTask.task_id == task_id)
        .where(SDPTask.is_deleted == "F")
    ).one()

    db_task.update_from_model(payload, db_user.cisco_cco_id, session)

    query_members = (
        QueryMembership()
        .add_orm_membership(SDPSubTask, payload.sub_task_ids)
        .add_orm_membership(SDPDeliverable, payload.deliverable_ids)
        .add_orm_membership(SDPAnchorDate, [payload.anchor_date_id])
        .add_orm_membership(SDPAnchorDateIterator, [payload.cycle_iterator_id])
        .build()
    )

    if session.exec(query_members).all():
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND, detail="One or more related ids not found"
        )

    create_dtm = update_dtm = datetime.now()
    created_by = updated_by = db_user.cisco_cco_id

    subtask_merger = MergeTargetRelations(
        target=SDPTask,
        target_id_col=SDPTask.task_id,
        secondary=SDPTaskToSubTask,
        secondary_target_col=SDPTaskToSubTask.task_id,
        secondary_rel_col=SDPTaskToSubTask.sub_task_id,
        related=SDPSubTask,
        related_id_col=SDPSubTask.sub_task_id,
    )

    existing_subtask_query = subtask_merger.build_existing_query(task_id)
    existing_subtasks = session.exec(existing_subtask_query).all()

    subtask_virtual_source = subtask_merger.build_virtual_source(
        target_id=task_id, proposed=payload.sub_task_ids, existing=existing_subtasks
    )
    merge_st = MergeInto(
        target=SDPTaskToSubTask.__table__,
        source=using_source(subtask_virtual_source),
        on=and_(
            SDPTaskToSubTask.task_id == subtask_virtual_source.c.task_id,
            SDPTaskToSubTask.sub_task_id == subtask_virtual_source.c.sub_task_id,
        ),
    )

    merge_st.when_matched_then_update().where(
        and_(
            SDPTaskToSubTask.is_deleted == "T",
            subtask_virtual_source.c.is_deleted == "F",
        )
    ).values(
        is_deleted=literal("F"),
        update_dtm=literal(update_dtm),
        updated_by=literal(updated_by),
    )
    merge_st.when_matched_then_update().where(
        and_(
            SDPTaskToSubTask.is_deleted == "F",
            subtask_virtual_source.c.is_deleted == "T",
        )
    ).values(
        is_deleted=literal("T"),
        update_dtm=literal(update_dtm),
        updated_by=literal(updated_by),
    )
    merge_st.when_not_matched_then_insert().values(
        task_id=subtask_virtual_source.c.task_id,
        sub_task_id=subtask_virtual_source.c.sub_task_id,
        create_dtm=literal(create_dtm),
        created_by=literal(created_by),
        is_deleted=subtask_virtual_source.c.is_deleted,
    )

    session.exec(merge_st)
    session.commit()

    # Deliverables

    deliverable_merger = MergeTargetRelations(
        target=SDPTask,
        target_id_col=SDPTask.task_id,
        secondary=SDPTaskToDeliverable,
        secondary_target_col=SDPTaskToDeliverable.task_id,
        secondary_rel_col=SDPTaskToDeliverable.deliverable_id,
        related=SDPDeliverable,
        related_id_col=SDPDeliverable.deliverable_id,
    )

    existing_deliverable_query = deliverable_merger.build_existing_query(task_id)
    existing_deliverables = session.exec(existing_deliverable_query).all()

    deliverable_virtual_source = deliverable_merger.build_virtual_source(
        target_id=task_id,
        proposed=payload.deliverable_ids,
        existing=existing_deliverables,
    )

    merge_deliverable = MergeInto(
        target=SDPTaskToDeliverable.__table__,
        source=using_source(deliverable_virtual_source),
        on=and_(
            SDPTaskToDeliverable.task_id == deliverable_virtual_source.c.task_id,
            SDPTaskToDeliverable.deliverable_id
            == deliverable_virtual_source.c.deliverable_id,
        ),
    )

    merge_deliverable.when_matched_then_update().where(
        and_(
            SDPTaskToDeliverable.is_deleted == "T",
            deliverable_virtual_source.c.is_deleted == "F",
        )
    ).values(
        is_deleted=literal("F"),
        update_dtm=literal(update_dtm),
        updated_by=literal(updated_by),
    )
    merge_deliverable.when_matched_then_update().where(
        and_(
            SDPTaskToDeliverable.is_deleted == "F",
            deliverable_virtual_source.c.is_deleted == "T",
        )
    ).values(
        is_deleted=literal("T"),
        update_dtm=literal(update_dtm),
        updated_by=literal(updated_by),
    )
    merge_deliverable.when_not_matched_then_insert().values(
        task_id=deliverable_virtual_source.c.task_id,
        deliverable_id=deliverable_virtual_source.c.deliverable_id,
        create_dtm=literal(create_dtm),
        created_by=literal(created_by),
        is_deleted=deliverable_virtual_source.c.is_deleted,
    )

    session.exec(merge_deliverable)
    session.commit()

    sdp_task_query = query_admin_sdp_task(task_id)
    db_sdp_task = session.exec(sdp_task_query).one()
    return db_sdp_task


@router.delete("/{task_id}")
def delete_sdp_task(
    task_id: int, db_user: GetUserDep, session: GetSessionDep
) -> Response:
    """Delete a SDPTask."""
    db_task = session.exec(
        select(SDPTask)
        .where(SDPTask.task_id == task_id)
        .where(SDPTask.is_deleted == "F")
    ).one()

    db_task.soft_delete(db_user.cisco_cco_id, session)

    # Cascade delete subtask relationships and deliverable relationships
    update_subtasks = (
        update(SDPTaskToSubTask)
        .where(SDPTaskToSubTask.task_id == task_id)
        .where(SDPTaskToSubTask.is_deleted == "F")
        .values(
            is_deleted="T", updated_by=db_user.cisco_cco_id, update_dtm=datetime.now()
        )
    )
    update_deliverables = (
        update(SDPTaskToDeliverable)
        .where(SDPTaskToDeliverable.task_id == task_id)
        .where(SDPTaskToDeliverable.is_deleted == "F")
        .values(
            is_deleted="T", updated_by=db_user.cisco_cco_id, update_dtm=datetime.now()
        )
    )

    session.exec(update_subtasks)
    session.exec(update_deliverables)
    session.commit()

    return JSONResponse(
        status_code=HTTP_200_OK,
        content={"success": True, "message": "Task deleted successfully"},
    )
