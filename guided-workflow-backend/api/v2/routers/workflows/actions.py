from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import joinedload
from sqlmodel import select

from api.dependencies import GetSessionDep
from api.v2.models import V2ActionItemAPI
from api.v2.orm import V2ActionItem

router = APIRouter()


@router.get("", response_model=list[V2ActionItemAPI])
def get_actions(
    session: GetSessionDep,
):
    """Get workflow actions for populating the task tree"""

    query = (
        select(V2ActionItem)
        .where(V2ActionItem.is_deleted == "F")
        .options(joinedload(V2ActionItem.children))
    )
    result = session.exec(query).unique().all()
    return result


@router.get("/{ui_enum}", response_model=V2ActionItemAPI)
def get_action(
    ui_enum: str,
    session: GetSessionDep,
):
    """Get workflow action by ui_enum"""

    query = (
        select(V2ActionItem)
        .where(V2ActionItem.ui_enum == ui_enum)
        .where(V2ActionItem.is_deleted == "F")
        .options(joinedload(V2ActionItem.children))
    )

    result = session.exec(query).unique().one_or_none()
    if result is None:
        raise HTTPException(status_code=404, detail="Action not found")

    return result
