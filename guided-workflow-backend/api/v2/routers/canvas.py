import json
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_, text
from sqlmodel import select
from starlette.status import (
    HTTP_200_OK,
    HTTP_304_NOT_MODIFIED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
)

from api.dependencies import (
    FlowV3ServiceDep,
    GetSessionDep,
    GetUserDep,
    fetch_engagement_links,
    is_support,
)
from api.dependencies.queries import fetch_engagement_evidence_uploads
from api.v2 import ServiceException
from api.v2.models import (
    UiEnum,
    V2CanvasEvidenceUploadResponse,
    V2CanvasParametersResponse,
    V2CanvasRead,
    V2EngagementLinks,
    V2SnapshotDataModel,
    V2SnapshotDataResponse,
    V3CanvasCreate,
    V3CanvasRebuild,
    safe_parse_collection,
)
from api.v2.orm import (
    V2AcatLink,
    V2CamEngagement,
    V2Canvas,
    V2DataSource,
    V2MceLink,
    V2SmartLink,
)
from api.v2.queries import (
    query_available_snapshots,
    query_canvas_external_runs,
    query_engagement_canvases,
    query_evidence_uploads,
    query_referenced_engagement_id,
)
from api.v2.services import ExternalServiceTracker

logger = logging.getLogger("api")

router = APIRouter()


create_canvas_tracker = ExternalServiceTracker(
    UiEnum.canvas_actions.value, "Creating Canvas"
)
CreateCanvasTracker = Annotated[ExternalServiceTracker, Depends(create_canvas_tracker)]
delete_canvas_tracker = ExternalServiceTracker(
    UiEnum.canvas_actions.value, "Deleting Canvas"
)
DeleteCanvasTracker = Annotated[ExternalServiceTracker, Depends(delete_canvas_tracker)]
FetchEngagementLinksDep = Annotated[V2EngagementLinks, Depends(fetch_engagement_links)]
FetchEngagementEvidenceUploadsDep = Annotated[
    list[V2CanvasEvidenceUploadResponse], Depends(fetch_engagement_evidence_uploads)
]


@router.get("/snapshots", response_model=V2SnapshotDataResponse)
def get_snapshots(
    session: GetSessionDep,
):
    query = query_available_snapshots()
    results = session.exec(query).mappings().all()
    if results is None:
        return []
    return safe_parse_collection(list[V2SnapshotDataModel], results)


@router.post("/rebuild", tags=["PrefectV3"])
def rebuild_canvas(
    payload: V3CanvasRebuild,
    db_user: GetUserDep,
    session: GetSessionDep,
    flow_service: FlowV3ServiceDep,
    tracker: CreateCanvasTracker,
    engagement_links: FetchEngagementLinksDep,
    evidence_uploads: FetchEngagementEvidenceUploadsDep,
) -> V2CanvasRead:
    """
    A user can rebuild a canvas from the UI. Their form will have defaults populated from a notification.
    They may alter the defaults and submit the form. However, the canvas_id and dc_engagement_id are immutable.
    """
    # Ensure user is associated with the engagement
    query = query_referenced_engagement_id(payload.dc_engagement_id, db_user.user_id)
    dc_engagement_id = session.exec(query).one_or_none()

    if not dc_engagement_id:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"Engagement {payload.dc_engagement_id} not found",
        )

    # Ensure canvas is not deleted / exists
    query = (
        select(V2Canvas)
        .where(V2Canvas.canvas_id == payload.canvas_id)
        .where(V2Canvas.is_deleted == "F")
        .where(V2Canvas.dc_engagement_id == dc_engagement_id)
    )
    db_canvas = session.exec(query).one_or_none()
    if not db_canvas:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="Canvas not found or you are not authorized to resubmit it",
        )

    db_canvas = db_canvas.update_from_model(
        model=payload,
        logged_user=db_user.cisco_cco_id,
        session=session,
    )

    payload._engagement_links = engagement_links
    payload._engagement_evidence_uploads = evidence_uploads

    with flow_service:
        try:
            db_canvas = flow_service.rebuild_canvas_flow(
                canvas_id=db_canvas.canvas_id,
                payload=payload,
                requestor=db_user,
                tracker=tracker,
            )
        except ServiceException as e:
            # ServiceExceptions are handled by the flow_service
            logger.exception("Error rebuilding canvas")
            raise HTTPException(
                status_code=e.code,
                detail=e.msg,
            ) from e
        except Exception as e:
            logger.exception("Error rebuilding canvas")
            raise HTTPException(
                status_code=500, detail="Error rebuilding canvas"
            ) from e
    return db_canvas


@router.post("", tags=["PrefectV3"], response_model=V2CanvasRead)
def create_canvas(
    payload: V3CanvasCreate,
    db_user: GetUserDep,
    session: GetSessionDep,
    tracker: CreateCanvasTracker,
    flow_service: FlowV3ServiceDep,
    engagement_links: FetchEngagementLinksDep,
    evidence_uploads: FetchEngagementEvidenceUploadsDep,
):
    # Ensure user is associated with the engagement
    query = query_referenced_engagement_id(payload.dc_engagement_id, db_user.user_id)
    dc_engagement_id = session.exec(query).one_or_none()
    if not dc_engagement_id:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"Either the engagement {payload.dc_engagement_id} does not exist or you are not authorized to create a canvas for it",
        )

    db_canvas = V2Canvas.create_from_model(
        model=payload,
        logged_user=db_user.cisco_cco_id,
        session=session,
    )

    payload._engagement_links = engagement_links
    payload._engagement_evidence_uploads = evidence_uploads

    with flow_service:
        try:
            db_canvas = flow_service.create_canvas_flow(
                canvas_id=db_canvas.canvas_id,
                payload=payload,
                requestor=db_user,
                tracker=tracker,
            )
        except ServiceException as e:
            # ServiceExceptions are handled by the flow_service
            logger.exception("Error creating canvas")
            db_canvas.soft_delete(db_user.cisco_cco_id, session)
            raise HTTPException(
                status_code=e.code,
                detail=e.msg,
            ) from e
        except Exception as e:
            logger.exception("Unhandled Error creating canvas")
            db_canvas.soft_delete(db_user.cisco_cco_id, session)
            raise HTTPException(status_code=500, detail="Error creating canvas") from e

    return db_canvas


@router.delete(
    "/{engagement_id}/canvas/{canvas_id}",
    response_model=V2CanvasRead,
    tags=["PrefectV3"],
)
def delete_canvas(
    engagement_id: int,
    canvas_id: int,
    session: GetSessionDep,
    db_user: GetUserDep,
    tracker: DeleteCanvasTracker,
    flow_service: FlowV3ServiceDep,
):
    query = (
        select(V2Canvas)
        .where(V2Canvas.is_deleted == "F")
        .join(
            V2CamEngagement,
            and_(
                V2Canvas.dc_engagement_id == V2CamEngagement.dc_engagement_id,
                V2CamEngagement.is_deleted == "F",
            ),
        )
        .where(V2Canvas.canvas_id == canvas_id)
        .where(V2CamEngagement.user_id == db_user.user_id)
    )

    db_canvas = session.exec(query).one_or_none()
    if not db_canvas:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="Canvas not found or you are not authorized to delete it",
        )

    logger.info(
        "Soft deleting canvas canvas_id=%s, engagement_id=%s, logged_user=%s",
        canvas_id,
        engagement_id,
        db_user.cisco_cco_id,
    )
    db_canvas.soft_delete(db_user.cisco_cco_id, session)

    db_notification = tracker.create_notification(
        dc_engagement_id=engagement_id,
        user_id=db_user.user_id,
        subject=f"Deleting Canvas #{canvas_id}",
        db_session=session,
    )
    with flow_service:
        flow_service.emit_canvas_deleted(
            canvas_id=canvas_id,
            dc_user_id=db_user.user_id,
            dc_engagement_id=engagement_id,
            notification_id=db_notification.notification_id,
            request_id=None,
        )
    return db_canvas


@router.get("/{engagement_id}/data_sources")
def get_data_sources(engagement_id: int, session: GetSessionDep):
    # noinspection PyArgumentList
    statement = (
        select(V2DataSource)
        .join(
            V2AcatLink.dc_engagement_id,
            (V2AcatLink.id == V2DataSource.remote_system_customer_identifier)
            & (V2DataSource.remote_system == "acat_customer_id"),
        )
        .where(V2AcatLink.dc_engagement_id == engagement_id)
        .union(
            select(V2DataSource)
            .join(
                V2MceLink.dc_engagement_id,
                (V2MceLink.id == V2DataSource.remote_system_customer_identifier)
                & (V2DataSource.remote_system == "mce_engagement_id"),
            )
            .where(V2MceLink.dc_engagement_id == engagement_id),
            select(V2DataSource)
            .join(
                V2SmartLink.dc_engagement_id,
                (V2SmartLink.id == V2DataSource.remote_system_customer_identifier)
                & (V2DataSource.remote_system == "mce_smart_account"),
            )
            .where(V2SmartLink.dc_engagement_id == engagement_id),
        )
        .order_by(V2DataSource.date_sourced.desc())
    )

    db_sources = session.exec(statement).all()
    return db_sources


@router.get(
    "/{engagement_id}/evidence_uploads",
    response_model=list[V2CanvasEvidenceUploadResponse],
)
def get_evidence_uploads(engagement_id: int, session: GetSessionDep):
    query = query_evidence_uploads(dc_engagement_id=engagement_id)
    results = session.exec(query).all()
    return results


@router.get("/{dc_engagement_id}", response_model=list[V2CanvasRead])
def get_engagement_canvas_data_v2(
    dc_engagement_id: int, session: GetSessionDep, db_user: GetUserDep
):
    """Get a list of canvases for a given engagement"""

    query = query_engagement_canvases(dc_engagement_id, db_user.cisco_cco_id)
    result = session.exec(query).scalars().all()
    return result


@router.get("/{canvas_id}/parameters", response_model=list[V2CanvasParametersResponse])
def get_canvas_creation_parameters(
    canvas_id: int,
    session: GetSessionDep,
):
    """
    For a given Canvas ID, return the parameters used to create the canvas
    """

    query = query_canvas_external_runs(canvas_id)
    result = [
        param
        for param in [r.canvas_parameters for r in session.exec(query).all()]
        if param is not None
    ]
    return safe_parse_collection(list[V2CanvasParametersResponse], result)


@router.get("/1/deleted", response_model=None, dependencies=[Depends(is_support)])
def get_deleted_canvas(
    session: GetSessionDep,
):
    stmt = text(
        """
    with canvas AS (
                 SELECT c.CANVAS_ID , c.DC_ENGAGEMENT_ID, c.CANVAS_NAME, c.CANVAS_DESC, c.UPDATED_BY, c.UPDATE_DTM
                    FROM DC_CANVAS_HDR c
                    WHERE c.IS_DELETED = 'T'
                ORDER BY c.UPDATE_DTM DESC
            )
            SELECT TO_JSON(
                OBJECT_CONSTRUCT_KEEP_NULL(
                     'dc_engagement_id',                        c.DC_ENGAGEMENT_ID,
                     'canvas_id',                               c.CANVAS_ID,
                     'canvas_name',                             c.CANVAS_NAME,
                     'canvas_desc',                             c.CANVAS_DESC,
                     'update_dtm',                              c.UPDATE_DTM,
                     'updated_by',                              c.UPDATED_BY
                )
            ) 
            FROM canvas c"""
    )
    result = session.exec(stmt).scalars().all()
    if not result:
        return []
    return [json.loads(r) for r in result]


@router.put(
    "/1/undelete/{canvas_id}",
    response_model=None,
    status_code=200,
    dependencies=[Depends(is_support)],
)
def undelete_canvas_v2(
    canvas_id: int,
    db_user: GetUserDep,
    session: GetSessionDep,
):
    stmt = select(V2Canvas).where(V2Canvas.canvas_id == canvas_id)
    db_canvas = session.exec(stmt).one_or_none()

    if not db_canvas:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="No Such Engagement",
        )
    else:
        db_canvas.is_deleted = "F"
        db_canvas.updated_by = db_user.cisco_cco_id

        session.add(db_canvas)
        session.commit()
        session.refresh(db_canvas)
        return db_canvas


@router.put("/{canvas_id}/enable", status_code=HTTP_200_OK)
def enable_canvas(
    canvas_id: int,
    session: GetSessionDep,
    user: GetUserDep,
) -> dict:
    """
    Enable a canvas that was soft-deactivated by dc-canvas-retention.

    Returns:
    - 200: Canvas enabled successfully
    - 304: Canvas already enabled (no change)
    - 403: Canvas name starts with '(DEACTIVATED)'
    - 404: Canvas not found or user lacks access (includes soft-deleted)
    """

    # Get canvas with access validation - same pattern as delete endpoint
    query = (
        select(V2Canvas)
        .where(V2Canvas.is_deleted == "F")
        .join(
            V2CamEngagement,
            and_(
                V2Canvas.dc_engagement_id == V2CamEngagement.dc_engagement_id,
                V2CamEngagement.is_deleted == "F",
            ),
        )
        .where(V2Canvas.canvas_id == canvas_id)
        .where(V2CamEngagement.user_id == user.user_id)
    )

    canvas_obj = session.exec(query).one_or_none()
    if not canvas_obj:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="Canvas not found or you are not authorized to access it",
        )

    # Business rule: Cannot enable deactivated canvases
    if canvas_obj.canvas_name.startswith("(DEACTIVATED)"):
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="Cannot enable canvas marked as deactivated",
        )

    # Return 304 if already enabled (no modification needed)
    if canvas_obj.enabled:
        logger.info(
            "Canvas enable attempt - already enabled: canvas_id=%d, canvas_name=%r, user=%r",
            canvas_id,
            canvas_obj.canvas_name,
            user.cisco_cco_id,
        )
        raise HTTPException(
            status_code=HTTP_304_NOT_MODIFIED, detail="Canvas is already enabled"
        )

    # Enable the canvas using ORM (update_dtm handled automatically by ORM)
    canvas_obj.enabled = True
    canvas_obj.updated_by = user.cisco_cco_id
    session.add(canvas_obj)
    session.commit()

    # Enhanced audit logging
    logger.info(
        "Canvas enabled successfully: canvas_id=%d, canvas_name=%r, user=%r, engagement_id=%d",
        canvas_id,
        canvas_obj.canvas_name,
        user.cisco_cco_id,
        canvas_obj.dc_engagement_id,
    )

    return {
        "canvas_id": canvas_id,
        "enabled": True,
        "message": "Canvas enabled successfully",
    }
