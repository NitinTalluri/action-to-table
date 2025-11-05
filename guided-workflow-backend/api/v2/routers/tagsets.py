import io
import logging
from datetime import date, datetime
from typing import Annotated

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import Integer, bindparam, func, text
from sqlmodel import select
from starlette.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_409_CONFLICT,
)

from api.dependencies import (
    AuthorizedEngagementPath,
    FlowV3ServiceDep,
    GetSessionDep,
    GetUserDep,
    S3ClientDep,
    is_support,
    require_admin,
)
from api.v2.models import (
    TextMessageCreate,
    UiEnum,
    V2CreateEngagementTagset,
    V2CreateGlobalTagset,
    V2TagsetResponse,
    V2TagsetResponseWithTags,
    V2UpdateEngagementTagset,
    V2UpdateGlobalTagset,
)
from api.v2.orm import JSONVarchar, V2Tagset
from api.v2.queries import (
    query_engagement_tagsets,
    query_engagement_tagsets_with_global,
    query_global_tagsets,
)
from api.v2.services import ExternalServiceTracker

logger = logging.getLogger("api")

router = APIRouter()

tagset_tracker = ExternalServiceTracker(
    UiEnum.general_notification.value, "New Tagset Created"
)
TagsetTrackerDep = Annotated[ExternalServiceTracker, Depends(tagset_tracker)]


@router.get("/{dc_engagement_id}", response_model=list[V2TagsetResponseWithTags])
def get_engagement_tagsets_v2(
    dc_engagement_id: str,
    referenced: AuthorizedEngagementPath,
    session: GetSessionDep,
):
    """Get the tagsets and related tags for an engagement"""

    dc_engagement_id = referenced.dc_engagement_id
    stmt = query_engagement_tagsets(engagement_id=dc_engagement_id)

    result = session.exec(stmt).scalars().all()
    return result


@router.get("/1/global", response_model=list[V2TagsetResponseWithTags])
def get_global_tagsets_v2(
    session: GetSessionDep,
):
    """
    Get tagsets and related tags for global scope
    """

    result = session.exec(query_global_tagsets()).scalars().all()
    return result


@router.get(
    "/{dc_engagement_id}/for_tagging",
    response_model=list[V2TagsetResponseWithTags],
)
def get_engagement_tagsets_v2_for_tagging(
    referenced: AuthorizedEngagementPath,
    session: GetSessionDep,
):
    """Get the tagsets and related tags for an engagement"""
    dc_engagement_id = referenced.dc_engagement_id

    stmt = query_engagement_tagsets_with_global(dc_engagement_id=dc_engagement_id)
    result = session.exec(stmt).scalars().all()
    return result


@router.get("/extract/{dc_engagement_id}")
def extract_engagement_tagsets_v2(
    referenced: AuthorizedEngagementPath,
    session: GetSessionDep,
    s3_client: S3ClientDep,
):
    """Get the tagsets and related tags for an engagement"""
    db_user, dc_engagement_id = referenced.db_user, referenced.dc_engagement_id

    get_tags_query = text(
        """ select ts.TAGSET_ID as Tag_Set_ID, ts.TAGSET_NAME as Tag_Set_Name, ts.scope, ts.TAGSET_DESC, t.tag_name as Tag_Name,t.tag_desc as Tag_Desc, t.tag_id as Tag_ID
                from DC_TAGSET ts
                    join DC_CAM_TO_ENGAGEMENT c on (c.DC_ENGAGEMENT_ID=ts.DC_ENGAGEMENT_ID )
                    join DC_USERS u on ( u.USER_ID=c.USER_ID)
                    join DC_TAGS t on (t.TAGSET_ID = ts.TAGSET_ID)
                where ts.DC_ENGAGEMENT_ID = :dc_engagement_id and u.USER_ID = :user_id
                  and ts.IS_DELETED = 'F' and t.IS_DELETED = 'F'

        union

          select ts.TAGSET_ID as Tag_Set_ID, ts.TAGSET_NAME as Tag_Set_Name, ts.scope, ts.TAGSET_DESC, t.tag_name as Tag_Name,t.tag_desc as Tag_Desc, t.tag_id as Tag_ID
          from DC_TAGSET ts
                    join DC_TAGS t on (t.TAGSET_ID = ts.TAGSET_ID)
                where ts.scope='Global'
                  and ts.IS_DELETED = 'F'
                  and ts.TAGSET_ID not in (3582)
                  and ts.IS_DELETED = 'F' and t.IS_DELETED = 'F'

    order by scope, Tag_Set_Name , Tag_Name"""
    ).bindparams(
        bindparam("dc_engagement_id", dc_engagement_id, type_=Integer),
        bindparam("user_id", db_user.user_id, type_=Integer),
    )
    df_tags = pd.read_sql(get_tags_query, session.connection())

    # Placeholder for InstanceID - Tag
    df_instance_tag = pd.DataFrame(columns=["Instance_ID", "Tag_ID"])

    # EngagementID
    df_engagement_id = pd.DataFrame(columns=["Engagement_ID"], data=[dc_engagement_id])

    # Hidden sheet with info
    df_info_sheet = pd.DataFrame(columns=["upload_type"], data=["DC_TAG_V1"])

    with io.BytesIO() as output:
        # noinspection PyTypeChecker,PydanticTypeChecker
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df_tags.to_excel(writer, sheet_name="Tag Sets - Tags", index=False)
            df_instance_tag.to_excel(
                writer, sheet_name="InstanceID - Tag mapping", index=False
            )
            df_engagement_id.to_excel(writer, sheet_name="EngagementID", index=False)
            df_info_sheet.to_excel(writer, sheet_name="info", index=False)

            for sheet_name in writer.sheets:
                writer.sheets[sheet_name].autofit()

            info_sheet = writer.sheets["info"]
            info_sheet.hide()

        data = output.getvalue()

    current_date = date.today()
    file_name = f"File_Upload_Template_{dc_engagement_id}_{current_date}.xlsx"

    try:
        s3_client.put_object(
            Bucket="dc-generic-upload-outputs",
            Key=f"extract-tags/{file_name}",
            Body=data,
        )
    except Exception:
        # We don't need to throw 500 here, as we can still return the file
        logger.exception("Error uploading file to S3")
    return Response(
        data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment;filename={file_name}"},
    )


@router.post("/{dc_engagement_id}", tags=["PrefectV3"], response_model=V2TagsetResponse)
def create_engagement_tagset_v2(
    referenced: AuthorizedEngagementPath,
    payload: V2CreateEngagementTagset,
    session: GetSessionDep,
    tracker: TagsetTrackerDep,
    flow_service: FlowV3ServiceDep,
):
    """
    Create a new tagset for an engagement.
    ---
    The submitted tagset name may differ from the name that is actually created.
    Any characters that do not match [a-zA-Z0-9_] will be replaced with an underscore.
    The tagset name will be checked against a list of reserved words.
    The tagset name will be checked against a list of reserved words.

    After a tagset is created:
    - It is not present in the static tags table. The static tags table will need to be updated to include the new tagset.
    - Since the static tags table is referenced by the canvas_thoughtspot_view, this view definition will need to be updated.
    - This additional processing is handled view Prefect
    """

    if not payload.dc_engagement_id == referenced.dc_engagement_id:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="Payload dc_engagement_id does not match path dc_engagement_id",
        )

    # User exists and has link to engagement
    db_user, dc_engagement_id = referenced.db_user, referenced.dc_engagement_id

    query_existing = (
        select(V2Tagset)
        .where(V2Tagset.dc_engagement_id == dc_engagement_id)
        .where(func.upper(V2Tagset.tagset_name) == payload.tagset_name.upper())
    )

    # Payload will already be transformed with clean_strings and exception will be raised if reserved word found
    existing_tagset = session.exec(query_existing).one_or_none()

    match existing_tagset:
        case None:
            db_tagset = V2Tagset.create_from_model(
                payload, db_user.cisco_cco_id, session
            )
            request_id = tracker.get_next_request_id(session)

            db_notification = tracker.create_notification(
                dc_engagement_id=dc_engagement_id,
                db_session=session,
                messages=[
                    TextMessageCreate(
                        type="text",
                        data=f"Tagset {db_tagset.tagset_name} created. Starting process to update static tags table and ThoughtSpot view.",
                    )
                ],
                user_id=db_user.user_id,
                request_id=request_id,
            )
            flow_service.emit_tagset_created(
                dc_engagement_id=dc_engagement_id,
                dc_user_id=db_user.user_id,
                notification_id=db_notification.notification_id,
                request_id=request_id,
            )
            return db_tagset
        case V2Tagset(is_deleted="T", tagset_id=tagset_id, tagset_name=tagset_name):
            # only documentation updating is deleted and description NOT the name

            logger.info(
                "Restoring tagset_id=%s, tagset_name=%s from deleted state",
                tagset_id,
                tagset_name,
            )
            db_tagset = existing_tagset.update_from_model(
                payload, db_user.cisco_cco_id, session
            )
            request_id = tracker.get_next_request_id(session)

            db_notification = tracker.create_notification(
                dc_engagement_id=dc_engagement_id,
                db_session=session,
                messages=[
                    TextMessageCreate(
                        type="text",
                        data=f"Tagset {db_tagset.tagset_name} created. Starting process to update static tags table and ThoughtSpot view.",
                    )
                ],
                user_id=db_user.user_id,
                request_id=request_id,
            )
            flow_service.emit_tagset_created(
                dc_engagement_id=dc_engagement_id,
                dc_user_id=db_user.user_id,
                notification_id=db_notification.notification_id,
                request_id=request_id,
            )
            return db_tagset
        case _:
            raise HTTPException(
                status_code=HTTP_409_CONFLICT,
                detail=f"Tagset with name '{payload.tagset_name}' already exists. Please choose a different name.",
            )


@router.patch("/{dc_engagement_id}/{tagset_id}", response_model=V2TagsetResponse)
def update_engagement_tagset_v2(
    referenced: AuthorizedEngagementPath,
    tagset_id: int,
    payload: V2UpdateEngagementTagset,
    session: GetSessionDep,
):
    """
    Update an existing tagset for an engagement

    Note: The tagset name cannot be updated.
    """

    if not payload.tagset_id == tagset_id:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="Payload tagset_id does not match path tagset_id",
        )
    db_user, dc_engagement_id = referenced.db_user, referenced.dc_engagement_id

    tagset_query = (
        select(V2Tagset)
        .where(V2Tagset.dc_engagement_id == dc_engagement_id)
        .where(V2Tagset.is_deleted == "F")
        .where(V2Tagset.tagset_id == tagset_id)
    )

    db_tagset = session.exec(tagset_query).one_or_none()
    if not db_tagset:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Tagset not found")

    db_tagset = db_tagset.update_from_model(payload, db_user.cisco_cco_id, session)
    return db_tagset


@router.post(
    "/1/global",
    response_model=V2TagsetResponse,
    dependencies=[Depends(require_admin)],
)
def create_global_tagset_v2(
    db_user: GetUserDep,
    payload: V2CreateGlobalTagset,
    session: GetSessionDep,
):
    if not payload.dc_engagement_id == 1:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="Global tagset must have dc_engagement_id = 1",
        )

    tagset_query = (
        select(V2Tagset)
        .where(V2Tagset.scope == "Global")
        .where(V2Tagset.dc_engagement_id == 1)
        .where(func.upper(V2Tagset.tagset_name) == payload.tagset_name.upper())
    )
    db_tagset = session.exec(tagset_query).one_or_none()

    match db_tagset:
        case None:
            db_tagset = V2Tagset.create_from_model(
                payload, db_user.cisco_cco_id, session
            )
            return db_tagset
        case V2Tagset(is_deleted="T", tagset_id=tagset_id, tagset_name=tagset_name):
            # only documentation updating is deleted and description NOT the name
            logger.info(
                "Restoring Global Tagset tagset_id=%s, tagset_name=%s from deleted state",
                tagset_id,
                tagset_name,
            )

            return db_tagset.update_from_model(payload, db_user.cisco_cco_id, session)

        case _:
            raise HTTPException(
                status_code=HTTP_409_CONFLICT,
                detail=f"Global Tagset with name '{payload.tagset_name}' already exists. Please choose a different name.",
            )


@router.patch(
    "/1/global/{tagset_id}",
    response_model=V2TagsetResponse,
    dependencies=[Depends(require_admin)],
)
def update_global_tagset_v2(
    tagset_id: int,
    payload: V2UpdateGlobalTagset,
    session: GetSessionDep,
    db_user: GetUserDep,
):
    """
    Update a global tagset
    """

    if not payload.tagset_id == tagset_id:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="Payload tagset_id does not match path tagset_id",
        )

    tagset_query = (
        select(V2Tagset)
        .where(V2Tagset.scope == "Global")
        .where(V2Tagset.is_deleted == "F")
        .where(V2Tagset.tagset_id == tagset_id)
        .where(V2Tagset.dc_engagement_id == 1)
    )

    db_tagset = session.exec(tagset_query).one_or_none()
    if not db_tagset:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Tagset not found")
    return db_tagset.update_from_model(payload, db_user.cisco_cco_id, session)


@router.delete(
    "/1/global/{tagset_id}",
    response_model=V2TagsetResponse,
    dependencies=[Depends(require_admin)],
)
def delete_global_tagset_v2(
    tagset_id: int,
    db_user: GetUserDep,
    session: GetSessionDep,
):
    """
    Delete a global tagset
    """
    tagset_query = (
        select(V2Tagset)
        .where(V2Tagset.scope == "Global")
        .where(V2Tagset.tagset_id == tagset_id)
    )

    db_tagset = session.exec(tagset_query).one_or_none()
    if not db_tagset:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Tagset not found")
    return db_tagset.soft_delete(db_user.cisco_cco_id, session)


@router.get(
    "/1/deleted",
    response_model=list[V2TagsetResponse],
    dependencies=[Depends(is_support)],
)
async def get_deleted_tagsets_v2(session: GetSessionDep):
    stmt = text(
        """
        WITH tagsets AS (
                SELECT ts.DC_ENGAGEMENT_ID, ts.TAGSET_ID, ts.TAGSET_NAME, ts.TAGSET_DESC, ts.scope,
                    ts.CARDINALITY, ts.TAGSET_TYPE, ts.UPDATE_DTM, ts.UPDATED_BY
                FROM DC_TAGSET ts
                WHERE ts.IS_DELETED = 'T' ORDER BY ts.UPDATE_DTM DESC
            )
            SELECT TO_JSON(
                OBJECT_CONSTRUCT_KEEP_NULL(
                        'dc_engagement_id',           c.DC_ENGAGEMENT_ID,
                        'tagset_id',                  c.TAGSET_ID,
                        'scope',                      c.SCOPE,
                        'cardinality',                c.CARDINALITY,
                        'tagset_type',                c.TAGSET_TYPE,
                        'tagset_name',                c.TAGSET_NAME,
                        'tagset_desc',                c.TAGSET_DESC,
                        'update_dtm',                 c.UPDATE_DTM,
                        'updated_by',                 c.UPDATED_BY
                )
            ) as tagset_row
                           FROM tagsets c
                           """
    ).columns(tagset_row=JSONVarchar)
    result = session.exec(stmt).scalars().all()
    return result


@router.put(
    "/1/undelete/{tagset_id}",
    response_model=V2TagsetResponse,
    status_code=200,
    dependencies=[Depends(is_support)],
)
def undelete_tagset_v2(
    tagset_id: int,
    session: GetSessionDep,
    db_user: GetUserDep,
):
    query_tagsets = (
        select(V2Tagset)
        .where(V2Tagset.tagset_id == tagset_id)
        .where(V2Tagset.is_deleted == "T")
    )
    db_tagset = session.exec(query_tagsets).one_or_none()

    if not db_tagset:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"Tagset with tagset_id {tagset_id} not found",
        )

    db_tagset.is_deleted = "F"
    db_tagset.updated_by = db_user.cisco_cco_id
    db_tagset.update_dtm = datetime.now()
    session.add(db_tagset)
    session.commit()
    session.refresh(db_tagset)
    return db_tagset
