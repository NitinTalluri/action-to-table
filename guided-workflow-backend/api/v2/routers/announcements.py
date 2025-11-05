import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from starlette.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT,
    HTTP_404_NOT_FOUND,
)

from api.dependencies import (
    GetSessionDep,
    GetSettingsDep,
    GetUserDep,
    require_admin,
)
from api.v2 import AnnouncementsService, ServiceException
from api.v2.models import (
    V2AnnouncementBase,
    V2AnnouncementRead,
    V2AnnouncementStatusBase,
    V2AnnouncementUpdate,
    safe_parse_collection,
)
from api.v2.queries import (
    query_announcement_by_id,
    query_announcements,
    query_user_announcements,
)

logger = logging.getLogger("api")
router = APIRouter()


@router.post(
    "",
    status_code=HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
def create_announcement(
    payload: V2AnnouncementBase, session: GetSessionDep, db_user: GetUserDep
) -> V2AnnouncementRead:
    """Create a new announcement."""

    with AnnouncementsService(session=session) as service:
        try:
            announcement_id = service.create_announcement(
                model=payload, requestor=db_user.cisco_cco_id
            )
            session.commit()
        except ServiceException as e:
            logger.exception(e)
            raise HTTPException(
                status_code=e.code,
                detail=e.msg,
            ) from e

    query = query_announcement_by_id(
        announcement_id=announcement_id, user_id=db_user.user_id
    )
    db_announcement = session.exec(query).mappings().one_or_none()
    return V2AnnouncementRead.parse_obj(db_announcement)


@router.get("", status_code=HTTP_200_OK)
def list_announcements(
    db_user: GetUserDep,
    session: GetSessionDep,
    settings: GetSettingsDep,
    dashboard_view: Optional[bool] = False,
) -> list[V2AnnouncementRead]:
    """
    Retrieve a list of announcements. Dashboard View is for typical user queries
    """

    query = (
        query_user_announcements(
            user_id=db_user.user_id,
            cisco_cco_id=db_user.cisco_cco_id,
            limit=settings.announcement_dashboard_limit,
        )
        if dashboard_view
        else query_announcements(user_id=db_user.user_id)
    )

    db_announcement = session.exec(query).mappings().all()

    return safe_parse_collection(list[V2AnnouncementRead], db_announcement)


@router.get("/{announcement_id}", status_code=HTTP_200_OK)
def get_announcement(
    db_user: GetUserDep,
    session: GetSessionDep,
    announcement_id: int,
) -> V2AnnouncementRead:
    """
    Retrieve a specific announcement by ID.
    """

    query = query_announcement_by_id(announcement_id, db_user.user_id)
    db_announcement = session.exec(query).one_or_none()

    if not db_announcement:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"Announcement ({announcement_id}) not found",
        )

    return db_announcement


@router.put(
    "/{announcement_id}",
    status_code=HTTP_200_OK,
    dependencies=[Depends(require_admin)],
)
def update_announcement(
    payload: V2AnnouncementUpdate,
    announcement_id: int,
    db_user: GetUserDep,
    session: GetSessionDep,
) -> V2AnnouncementRead:
    """
    Update an existing announcement.
    """

    with AnnouncementsService(session=session) as service:
        try:
            service.update_announcement(
                announcement_id, model=payload, requestor=db_user.cisco_cco_id
            )
            session.commit()
        except ServiceException as e:
            logger.exception(e)
            raise HTTPException(
                status_code=e.code,
                detail=e.msg,
            ) from e

    query = query_announcement_by_id(announcement_id, db_user.user_id)
    db_announcement = session.exec(query).one_or_none()

    if not db_announcement:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"Announcement ({announcement_id}) not found",
        )

    return db_announcement


@router.put("/{announcement_id}/status", status_code=HTTP_200_OK)
def update_announcement_status(
    payload: V2AnnouncementStatusBase,
    announcement_id: int,
    db_user: GetUserDep,
    session: GetSessionDep,
) -> V2AnnouncementRead:
    """
    Update an existing announcement status for a User.
    """

    with AnnouncementsService(session=session) as service:
        try:
            service.track_announcement_dismissal(
                announcement_id=announcement_id,
                user_id=db_user.user_id,
                requestor=db_user.cisco_cco_id,
                is_dismissed=payload.is_dismissed,
            )
            session.commit()
        except ServiceException as e:
            logger.exception(e)
            raise HTTPException(
                status_code=e.code,
                detail=e.msg,
            ) from e

    query = query_announcement_by_id(announcement_id, db_user.user_id)
    db_announcement = session.exec(query).one_or_none()

    if not db_announcement:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"Announcement ({announcement_id}) not found",
        )
    return db_announcement


@router.delete(
    "/{announcement_id}",
    response_model=None,
    status_code=HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_admin)],
)
def delete_announcement(
    announcement_id: int,
    db_user: GetUserDep,
    session: GetSessionDep,
) -> None:
    """
    Delete an existing Announcement
    """

    with AnnouncementsService(session=session) as service:
        try:
            service.delete_announcement(
                announcement_id=announcement_id, requestor=db_user.cisco_cco_id
            )
            session.commit()
        except ServiceException as e:
            logger.exception(e)
            raise HTTPException(
                status_code=e.code,
            ) from e
