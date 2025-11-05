import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, text
from sqlmodel import select
from starlette.status import HTTP_403_FORBIDDEN, HTTP_404_NOT_FOUND, HTTP_409_CONFLICT

from api.dependencies import (
    GetSessionDep,
    GetUserDep,
    UserRequest,
    is_support,
    require_admin,
)
from api.v2.models import V2TagRead, V2TagUpdate, V2TagWrite
from api.v2.orm import V2CamEngagement, V2Engagement, V2Tags, V2Tagset, V2User
from api.v2.queries import GET_logged_user, query_users_engagements

router = APIRouter()


@router.get("/{dc_engagement_id}", response_model=list[V2TagRead])
async def get_engagement_tags_v2(
    dc_engagement_id: int,
    req: UserRequest,
    session: GetSessionDep,
    logged_user: Optional[str] = None,
):
    """Get the tags for an engagement"""

    logged_user = GET_logged_user(req, logged_user)

    user_engagements_query = query_users_engagements(logged_user).where(
        V2Engagement.dc_engagement_id == dc_engagement_id
    )

    user_engagement = session.exec(user_engagements_query).one_or_none()
    if not user_engagement:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND, detail="Engagement not found"
        )

    engagement_tags_select = select(
        *V2Tags.__table__.columns,
        V2Tagset.tagset_id,
    )
    engagement_tags_query = (
        engagement_tags_select.where(V2Tags.is_deleted != "T")
        .join(V2Tagset)
        .where(V2Tagset.dc_engagement_id == dc_engagement_id)
        .where(V2Tagset.is_deleted != "T")
        .where(V2Tagset.dc_engagement_id == user_engagement.dc_engagement_id)
    )
    result = session.exec(engagement_tags_query).all()
    return [V2TagRead.from_orm(row) for row in result]


@router.post("/{dc_engagement_id}", response_model=V2TagRead)
async def create_engagement_tag_v2(
    dc_engagement_id: int,
    req: UserRequest,
    session: GetSessionDep,
    tag: V2TagWrite,
    logged_user: Optional[str] = None,
):
    """Create a new tag for an engagement"""
    logged_user = GET_logged_user(req, logged_user)
    user_engagements_query = query_users_engagements(logged_user).where(
        V2Engagement.dc_engagement_id == dc_engagement_id
    )

    user_engagement = session.exec(user_engagements_query).one_or_none()
    if not user_engagement:
        raise HTTPException(status_code=404, detail="Engagement not found")

    tagset_query = (
        select(V2Tagset)
        .join(V2Tags)
        .where(V2Tagset.dc_engagement_id == user_engagement.dc_engagement_id)
        .where(V2Tagset.tagset_id == tag.tagset_id)
        .where(V2Tagset.is_deleted == "F")
        .where(func.upper(V2Tags.tag_name) == func.upper(tag.tag_name))
    )

    tagset = session.exec(tagset_query).one_or_none()
    if not tagset:
        db_tag = V2Tags.create_from_model(tag, logged_user, session)
        return V2TagRead.from_orm(db_tag)
    else:
        raise HTTPException(
            status_code=HTTP_409_CONFLICT, detail="duplicate name tagfound"
        )


@router.patch("/{dc_engagement_id}/{tag_id}", response_model=V2TagRead)
async def update_engagement_tag_v2(
    dc_engagement_id: int,
    tag_id: int,
    req: UserRequest,
    session: GetSessionDep,
    tag: V2TagUpdate,
    logged_user: Optional[str] = None,
):
    """Update an existing tag for an engagement"""
    logged_user = GET_logged_user(req, logged_user)

    user_engagements_query = query_users_engagements(logged_user).where(
        V2Engagement.dc_engagement_id == dc_engagement_id
    )

    user_engagement = session.exec(user_engagements_query).one_or_none()
    if not user_engagement:
        raise HTTPException(status_code=404, detail="Engagement not found")

    tag_query = (
        select(V2Tags).where(V2Tags.is_deleted != "T").where(V2Tags.tag_id == tag_id)
    )

    db_tag = session.exec(tag_query).one_or_none()
    if not db_tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    # todo this can create duplicate names but, thats the way it goes
    db_tag.update_from_model(tag, logged_user, session)

    return V2TagRead.from_orm(db_tag)


@router.delete("/{tag_id}", response_model=V2TagRead)
async def delete_engagement_tag_v2(
    tag_id: int,
    req: UserRequest,
    session: GetSessionDep,
    logged_user: Optional[str] = None,
):
    """Delete (soft-delete) an existing tag for an engagement"""
    logged_user = GET_logged_user(req, logged_user)

    # We need to get the relation of the engagement to the tag to check if the user can delete it

    tag_query = (
        select(
            V2Tags,
            V2Engagement.dc_engagement_id.label("dc_engagement_id"),  # type: ignore
        )
        .select_from(V2Tags)
        .where(V2Tags.tag_id == tag_id)
        .join(V2Tagset)
        .join(V2Engagement)
        .join(V2CamEngagement)
        .join(V2User)
        .where(V2User.cisco_cco_id == logged_user)
    )

    db_row = session.exec(tag_query).one_or_none()

    if not db_row:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Tag not found")
    db_tag, dc_engagement_id = db_row
    db_tag.soft_delete(logged_user, session)

    return V2TagRead.from_orm(db_tag)


#################################################


@router.post(
    "/1/global", response_model=V2TagRead, dependencies=[Depends(require_admin)]
)
async def create_engagement_tag_v2_GLOBAL(
    db_user: GetUserDep,
    session: GetSessionDep,
    tag: V2TagWrite,
):
    tagset_query = (
        select(V2Tagset)
        .where(V2Tagset.is_deleted == "F")
        .where(V2Tagset.scope == "Global")
        .where(V2Tagset.tagset_id == tag.tagset_id)
    )
    tagset = session.exec(tagset_query).one_or_none()
    if not tagset:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND, detail="Global Tagset not found"
        )
    db_tag = V2Tags.create_from_model(tag, db_user.cisco_cco_id, session)

    return V2TagRead.from_orm(db_tag)


@router.patch(
    "/1/global/{tag_id}",
    response_model=V2TagRead,
    dependencies=[Depends(require_admin)],
)
async def update_engagement_tag_v2_GLOBAL(
    tag_id: int, db_user: GetUserDep, session: GetSessionDep, tag: V2TagUpdate
):
    tagset_query = (
        select(V2Tagset)
        .join(V2Tags)
        .where(V2Tagset.is_deleted == "F")
        .where(V2Tagset.scope == "Global")
        .where(V2Tags.tag_id == tag_id)
    )
    tagset = session.exec(tagset_query).one_or_none()
    if not tagset:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND, detail="Global Tagset not found"
        )

    tag_query = (
        select(V2Tags).where(V2Tags.is_deleted != "T").where(V2Tags.tag_id == tag_id)
    )
    db_tag = session.exec(tag_query).one_or_none()
    if not db_tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    db_tag.update_from_model(tag, db_user.cisco_cco_id, session)

    return V2TagRead.from_orm(db_tag)


@router.delete(
    "/1/global/{tag_id}",
    response_model=V2TagRead,
    dependencies=[Depends(require_admin)],
)
async def delete_engagement_tags_v2_GLOBAL(
    tag_id: int,
    session: GetSessionDep,
    db_user: GetUserDep,
):
    tagset_query = (
        select(V2Tagset)
        .join(V2Tags)
        .where(V2Tagset.is_deleted == "F")
        .where(V2Tagset.scope == "Global")
        .where(V2Tags.tag_id == tag_id)
    )
    tagset = session.exec(tagset_query).one_or_none()
    if not tagset:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND, detail="Global Tagset not found"
        )

    tag_query = (
        select(V2Tags).where(V2Tags.is_deleted != "T").where(V2Tags.tag_id == tag_id)
    )
    db_tag = session.exec(tag_query).one_or_none()
    if not db_tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    db_tag.soft_delete(db_user.cisco_cco_id, session)
    return V2TagRead.from_orm(db_tag)


@router.get("/1/deleted", response_model=None, dependencies=[Depends(is_support)])
async def get_deleted_engagement_tags_v2(
    session: GetSessionDep,
):
    stmt = text("""
        WITH tagsets AS 
        (
            SELECT ts.DC_ENGAGEMENT_ID, ts.TAGSET_ID, ts.TAGSET_NAME, ts.TAGSET_DESC, ts.scope, ts.CARDINALITY, ts.TAGSET_TYPE,
                   t.TAG_ID, t.TAG_NAME, t.TAG_DESC, t.UPDATE_DTM, t.UPDATED_BY
                   FROM DC_TAGSET ts JOIN DC_tags t ON (ts.TAGSET_ID=t.TAGSET_ID)
                   WHERE t.IS_DELETED = 'T'
            ORDER BY t.UPDATE_DTM DESC
            )
            select TO_JSON(
                OBJECT_CONSTRUCT_KEEP_NULL(
                       'dc_engagement_id',                 c.DC_ENGAGEMENT_ID,
                       'tagset_id',                        c.TAGSET_ID,
                       'scope',                            c.scope,
                       'cardinality',                      c.cardinality,
                       'tagset_type',                      c.tagset_type,
                       'tag_id',                           c.TAG_ID,
                       'tag_name',                         c.TAG_NAME,
                       'tag_desc',                         c.TAG_DESC,
                       'tagset_name',                      c.TAG_ID,
                       'update_dtm',                       c.update_dtm,
                       'updated_by',                       c.updated_by
                    )
                )
                from tagsets c
        """)
    result = session.exec(stmt).scalars().all()
    if not result:
        return []
    return [json.loads(row) for row in result]


@router.put(
    "/1/undelete/{tag_id}",
    response_model=None,
    status_code=200,
    dependencies=[Depends(is_support)],
)
async def undelete_tags_v2(
    tag_id: int,
    db_user: GetUserDep,
    session: GetSessionDep,
):
    stmt = select(V2Tags).where(V2Tags.tag_id == tag_id)
    db_tag = session.exec(stmt).one_or_none()

    if not db_tag:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="No Such Engagement",
        )

    db_tag.is_deleted = "F"
    db_tag.updated_by = db_user.cisco_cco_id
    session.add(db_tag)
    session.commit()
    session.refresh(db_tag)
    return db_tag
