import logging

from fastapi import APIRouter, HTTPException
from sqlalchemy import func
from sqlmodel import select
from starlette.status import HTTP_409_CONFLICT

from api.dependencies import GetSessionDep, GetUserDep
from api.v2.models import AdminSDPLifeCycle as SDPLifeCycleModel
from api.v2.models import AdminSDPLifeCycleEdit
from api.v2.orm.admin import SDPLifeCycle

router = APIRouter()

logger = logging.getLogger("api")


@router.get("/{life_cycle_id}", response_model=SDPLifeCycleModel)
def get_sdp_life_cycle(life_cycle_id: int, session: GetSessionDep):
    """Get a SDP Life Cycle by ID"""
    query = (
        select(SDPLifeCycle)
        .where(SDPLifeCycle.lifecycle_id == life_cycle_id)
        .where(SDPLifeCycle.is_deleted == "F")
    )
    result = session.exec(query).one_or_none()

    if not result:
        raise HTTPException(
            status_code=404, detail=f"Life Cycle with ID {life_cycle_id} not found"
        )

    return result


@router.post("/", response_model=SDPLifeCycleModel)
def create_sdp_life_cycle(
    payload: AdminSDPLifeCycleEdit, session: GetSessionDep, db_user: GetUserDep
):
    db_life_cycle = session.exec(
        select(SDPLifeCycle).where(
            SDPLifeCycle.lifecycle_desc == payload.lifecycle_desc
        )
    ).one_or_none()

    def make_or_restore(existing):
        match existing:
            case None:
                max_id = (
                    session.exec(select(func.max(SDPLifeCycle.lifecycle_id))).scalar()
                    or 0
                )
                db_life_cycle_inner = SDPLifeCycle(
                    lifecycle_id=max_id + 1,
                    created_by=db_user.cisco_cco_id,
                    **payload.dict(),
                )
                session.add(db_life_cycle_inner)
                session.commit()
                session.refresh(db_life_cycle_inner)
                return db_life_cycle_inner
            case SDPLifeCycle(is_deleted="F"):
                raise HTTPException(
                    status_code=HTTP_409_CONFLICT,
                    detail=f"SDPLifeCycle with this description {payload.lifecycle_desc} already exists",
                )
            case SDPLifeCycle(is_deleted="T"):
                logger.info("Restoring SDPLifeCycle %s", existing.lifecycle_id)
                existing.is_deleted = "F"
                existing.lifecycle_doc_link = payload.lifecycle_doc_link
                existing.updated_by = db_user.cisco_cco_id
                session.add(existing)
                session.commit()
                session.refresh(existing)
                return existing

    db_result = make_or_restore(db_life_cycle)

    return db_result


@router.patch("/{lifecycle_id}", response_model=SDPLifeCycleModel)
def edit_sdp_lifecycle(
    payload: AdminSDPLifeCycleEdit,
    db_user: GetUserDep,
    session: GetSessionDep,
    lifecycle_id: int,
):
    """Edit a SDPLifeCycle."""
    db_life_cycle = session.exec(
        select(SDPLifeCycle)
        .where(SDPLifeCycle.lifecycle_id == lifecycle_id)
        .where(SDPLifeCycle.is_deleted == "F")
    ).one()

    db_existing_life_cycle = session.exec(
        select(SDPLifeCycle)
        .where(SDPLifeCycle.life_cycle_desc == payload.lifecycle_desc)
        .where(SDPLifeCycle.lifecycle_id != lifecycle_id)
    ).one_or_none()

    if db_existing_life_cycle:
        raise HTTPException(
            status_code=HTTP_409_CONFLICT,
            detail=f"A SDPLifeCycle [{db_existing_life_cycle!r}] with this description already exists",
        )

    db_life_cycle.update_from_model(payload, db_user.cisco_cco_id, session)
    return db_life_cycle


@router.delete("/{lifecycle_id}", response_model=SDPLifeCycleModel)
def delete_sdp_life_cycle(
    lifecycle_id: int, session: GetSessionDep, db_user: GetUserDep
):
    """Delete a SDPLifeCycle by ID"""
    db_lifecycle = session.exec(
        select(SDPLifeCycle)
        .where(SDPLifeCycle.life_cycle_id == lifecycle_id)
        .where(SDPLifeCycle.is_deleted == "F")
    ).one()

    db_lifecycle.soft_delete(db_user.cisco_cco_id, session)
    return db_lifecycle
