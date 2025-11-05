from typing import Optional, Type, Union

from fastapi import APIRouter, HTTPException
from sqlmodel import select
from starlette.status import HTTP_403_FORBIDDEN, HTTP_404_NOT_FOUND, HTTP_409_CONFLICT
from toolz import groupby

from api.dependencies import GetSessionDep, UserRequest
from api.v2.models import (
    V2AcatLinkBase,
    V2AcatLinkDelete,
    V2AcatLinkRead,
    V2AcatLinkUpdate,
    V2AcatLinkWrite,
    V2EngagementLinks,
    V2GenericLinkDelete,
    V2GenericLinkRead,
    V2GenericLinkUpdate,
    V2GenericLinkWrite,
    V2LinkType,
    V2MceLinkBase,
    V2MceLinkDelete,
    V2MceLinkRead,
    V2MceLinkUpdate,
    V2MceLinkWrite,
    V2PartyLinkBase,
    V2PartyLinkDelete,
    V2PartyLinkRead,
    V2PartyLinkUpdate,
    V2PartyLinkWrite,
    V2SmartLinkBase,
    V2SmartLinkDelete,
    V2SmartLinkRead,
    V2SmartLinkUpdate,
    V2SmartLinkWrite,
)
from api.v2.orm import V2AcatLink, V2Engagement, V2MceLink, V2PartyLink, V2SmartLink
from api.v2.queries import GET_logged_user, query_users_engagements
from api.v2.queries.links import query_engagement_links

router = APIRouter()

LinkBases = Union[V2AcatLinkBase, V2MceLinkBase, V2PartyLinkBase, V2SmartLinkBase]
LinkWrites = Union[V2AcatLinkWrite, V2MceLinkWrite, V2PartyLinkWrite, V2SmartLinkWrite]
LinkUpdates = Union[
    V2AcatLinkUpdate, V2MceLinkUpdate, V2PartyLinkUpdate, V2SmartLinkUpdate
]
LinkReads = Union[V2AcatLinkRead, V2MceLinkRead, V2PartyLinkRead, V2SmartLinkRead]
LinkDeletes = Union[
    V2AcatLinkDelete, V2MceLinkDelete, V2PartyLinkDelete, V2SmartLinkDelete
]
LinkOrm = Union[V2AcatLink, V2MceLink, V2PartyLink, V2SmartLink]


def model_to_orm(model: LinkBases) -> Type[LinkOrm]:
    """
    Given a link model, return the corresponding ORM class
    """
    link_type = model.link_type
    if link_type == "acat_links":
        return V2AcatLink
    elif link_type == "mce_links":
        return V2MceLink
    elif link_type == "party_links":
        return V2PartyLink
    elif link_type == "smart_links":
        return V2SmartLink
    else:
        raise ValueError(f"Invalid link type: {link_type}")


@router.get("/{dc_engagement_id}", response_model=V2EngagementLinks)
async def get_engagement_links_v2(
    dc_engagement_id: int,
    session: GetSessionDep,
):
    """Retrieve all externally linked identifiers for an engagement"""

    query = query_engagement_links(dc_engagement_id=dc_engagement_id)
    db_links = session.exec(query).mappings().all()

    if not db_links:
        return V2EngagementLinks()

    # Group the links by type

    rows_by_type = groupby(lambda row: row["link_type"], db_links)

    return V2EngagementLinks(
        acat_links=rows_by_type.get("acat_links", []),
        mce_links=rows_by_type.get("mce_links", []),
        party_links=rows_by_type.get("party_links", []),
        smart_links=rows_by_type.get("smart_links", []),
    )


async def create_generic_link(
    dc_engagement_id: int,
    link: LinkWrites,
    req: UserRequest,
    session: GetSessionDep,
    logged_user: Optional[str] = None,
) -> LinkOrm:
    """
    Create a generic link
    """
    logged_user: str = GET_logged_user(req, logged_user)

    # Get the user's engagements
    user_engagements_query = query_users_engagements(logged_user).where(
        V2Engagement.dc_engagement_id == dc_engagement_id
    )

    db_engagement = session.exec(user_engagements_query).one_or_none()
    if db_engagement is None:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="You don't have access to this engagement",
        )

    orm_cls = model_to_orm(link)

    # Check if the link already exists
    db_link_query = (
        select(orm_cls)
        .where(orm_cls.id == link.id)
        .where(orm_cls.dc_engagement_id == link.dc_engagement_id)
    )
    db_link = session.exec(db_link_query).one_or_none()

    if db_link is None:
        db_link = orm_cls.create_from_model(link, logged_user, session)
        return db_link
    elif db_link.is_deleted == "T":
        db_link.update_from_model(link, logged_user, session)
        return db_link
    else:
        raise HTTPException(
            status_code=HTTP_409_CONFLICT, detail=f"Link {link.id=} already exists"
        )


@router.post("/{dc_engagement_id}/{link_type}", response_model=LinkReads)
async def v2_create_link(
    dc_engagement_id: int,
    link_type: V2LinkType,
    link: LinkWrites,
    req: UserRequest,
    session: GetSessionDep,
    logged_user: Optional[str] = None,
):
    logged_user: str = GET_logged_user(req, logged_user)
    link_data = {
        **link.dict(),
        "dc_engagement_id": dc_engagement_id,
        "link_type": link_type,
    }
    link_model = V2GenericLinkWrite.parse_obj(link_data).__root__
    db_link = await create_generic_link(
        dc_engagement_id, link_model, req, session, logged_user
    )
    link_response = V2GenericLinkRead.parse_obj(
        {
            "link_type": link_type,
            "id": db_link.id,
            "dc_engagement_id": db_link.dc_engagement_id,
        }
    ).__root__
    return link_response


async def update_generic_link(
    dc_engagement_id: int,
    link_id: int,
    link: LinkUpdates,
    req: UserRequest,
    session: GetSessionDep,
    logged_user: Optional[str] = None,
):
    logged_user = GET_logged_user(req, logged_user)

    # Check that the user has access to the engagement
    user_engagements_query = query_users_engagements(logged_user).where(
        V2Engagement.dc_engagement_id == dc_engagement_id
    )

    db_engagement = session.exec(user_engagements_query).one_or_none()
    if db_engagement is None:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="User does not have access to this engagement",
        )

    db_cls = model_to_orm(link)

    db_link_query = (
        select(db_cls)
        .where(db_cls.id == link_id)
        .where(db_cls.dc_engagement_id == dc_engagement_id)
        .where(db_cls.is_deleted == "F")
    )

    db_link = session.exec(db_link_query).one_or_none()

    if db_link is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND, detail=f"Link Id {link_id} not found"
        )

    return db_link.update_from_model(link, logged_user, session)


@router.patch("/{dc_engagement_id}/{link_type}/{link_id}", response_model=LinkReads)
async def v2_update_link(
    dc_engagement_id: int,
    link_type: V2LinkType,
    link: LinkUpdates,
    link_id: int,
    req: UserRequest,
    session: GetSessionDep,
    logged_user: Optional[str] = None,
):
    logged_user: str = GET_logged_user(req, logged_user)
    link_data = {
        **link.dict(),
        "dc_engagement_id": dc_engagement_id,
        "link_type": link_type,
    }
    link_model = V2GenericLinkUpdate.parse_obj(link_data).__root__
    db_link = await update_generic_link(
        dc_engagement_id,
        link_id=link_id,
        link=link_model,
        req=req,
        session=session,
        logged_user=logged_user,
    )

    link_response = V2GenericLinkRead.parse_obj(
        {
            "link_type": link_type,
            "id": db_link.id,
            "dc_engagement_id": db_link.dc_engagement_id,
        }
    ).__root__
    return link_response


async def delete_generic_link(
    dc_engagement_id: int,
    link: LinkDeletes,
    req: UserRequest,
    session: GetSessionDep,
    logged_user: Optional[str] = None,
) -> LinkOrm:
    logged_user = GET_logged_user(req, logged_user)

    # Check that the user has access to the engagement

    user_engagements_query = query_users_engagements(logged_user).where(
        V2Engagement.dc_engagement_id == dc_engagement_id
    )
    db_engagement = session.exec(user_engagements_query).one_or_none()
    if db_engagement is None:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="User does not have access to this engagement",
        )

    db_cls = model_to_orm(link)

    db_link_query = (
        select(db_cls)
        .where(db_cls.id == link.id)
        .where(db_cls.dc_engagement_id == dc_engagement_id)
        .where(db_cls.is_deleted == "F")
    )

    db_link = session.exec(db_link_query).one_or_none()
    if not db_link:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND, detail=f"Link Id {link.id} not found"
        )
    db_link.soft_delete(logged_user, session)
    return db_link


@router.delete("/{dc_engagement_id}/{link_type}/{link_id}", response_model=LinkDeletes)
async def v2_delete_link(
    dc_engagement_id: int,
    link_type: V2LinkType,
    link_id: int,
    req: UserRequest,
    session: GetSessionDep,
    logged_user: Optional[str] = None,
):
    logged_user: str = GET_logged_user(req, logged_user)
    link_data = {
        "id": link_id,
        "dc_engagement_id": dc_engagement_id,
        "link_type": link_type,
    }
    link_model = V2GenericLinkDelete.parse_obj(link_data).__root__
    db_link = await delete_generic_link(
        dc_engagement_id,
        link=link_model,
        req=req,
        session=session,
        logged_user=logged_user,
    )
    link_response = V2GenericLinkDelete.parse_obj(
        {
            "link_type": link_type,
            "id": db_link.id,
            "dc_engagement_id": db_link.dc_engagement_id,
        }
    ).__root__
    return link_response
