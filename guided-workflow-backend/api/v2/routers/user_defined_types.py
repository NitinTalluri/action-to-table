import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from sqlmodel import select

from api.dependencies import (
    AuthorizedEngagementBody,
    AuthorizedEngagementPath,
    GetSessionDep,
)
from api.v2.models import (
    V2UserDefinedType,
    V2UserDefinedTypeCreate,
    V2UserDefinedTypeDelete,
    V2UserDefinedTypeEdit,
)
from api.v2.orm import V2UserDefinedType as V2UserDefinedTypeORM

router = APIRouter()

logger = logging.getLogger("api")


@router.get("/{dc_engagement_id}", response_model=list[V2UserDefinedType])
def get_user_defined_types(
    session: GetSessionDep,
    referenced: AuthorizedEngagementPath,
    field_name: Optional[str] = None,
):
    """
    Get user defined types for a given engagement. Field name is optional but can be used to filter the results.
    """

    query = (
        select(V2UserDefinedTypeORM)
        .where(V2UserDefinedTypeORM.dc_engagement_id == referenced.dc_engagement_id)
        .where(V2UserDefinedTypeORM.is_deleted == "F")
    )
    if field_name:
        query = query.where(V2UserDefinedTypeORM.field_name == field_name)
    db_types = session.exec(query).all()
    return db_types


@router.post("", response_model=V2UserDefinedType)
def create_user_defined_type(
    session: GetSessionDep,
    referenced: AuthorizedEngagementBody,
    payload: V2UserDefinedTypeCreate,
):
    """
    Create a user defined type for a given engagement
    """

    _db_user, logged_user = referenced.db_user, referenced.db_user.cisco_cco_id

    # Check if there is already a user defined type with the same field_name and value that is deleted

    query_existing = (
        select(V2UserDefinedTypeORM)
        .where(V2UserDefinedTypeORM.dc_engagement_id == payload.dc_engagement_id)
        .where(V2UserDefinedTypeORM.field_name == payload.field_name)
        .where(V2UserDefinedTypeORM.value == payload.value)
    )

    existing = session.exec(query_existing).one_or_none()
    match existing:
        case None:
            db_model = V2UserDefinedTypeORM.create_from_model(
                payload, logged_user, session
            )
            return db_model
        case V2UserDefinedTypeORM(is_deleted="F"):
            raise HTTPException(
                status_code=409, detail="User defined type already exists"
            )
        case V2UserDefinedTypeORM(is_deleted="T"):
            existing.is_deleted = "F"
            session.add(existing)
            session.commit()
            return existing
        case _:
            logger.error("Logic Error - Unexpected case")
            raise HTTPException(status_code=500, detail="Unexpected error")


@router.delete("", response_model=V2UserDefinedType)
def delete_user_defined_type(
    session: GetSessionDep,
    referenced: AuthorizedEngagementBody,
    payload: V2UserDefinedTypeDelete,
):
    """
    Delete a user defined type for a given engagement
    """

    # User has permission for the engagement
    _db_user, logged_user = referenced.db_user, referenced.db_user.cisco_cco_id

    # Query the user defined type to delete

    udt_query = (
        select(V2UserDefinedTypeORM)
        .where(V2UserDefinedTypeORM.id == payload.id)
        .where(V2UserDefinedTypeORM.dc_engagement_id == payload.dc_engagement_id)
        .where(V2UserDefinedTypeORM.is_deleted == "F")
    )

    db_udt = session.exec(udt_query).one_or_none()
    if not db_udt:
        raise HTTPException(status_code=404, detail="User defined type not found")

    db_udt.soft_delete(logged_user, session)
    return db_udt


@router.patch("", response_model=V2UserDefinedType)
def edit_user_defined_type(
    session: GetSessionDep,
    referenced: AuthorizedEngagementBody,
    payload: V2UserDefinedTypeEdit,
):
    """
    Edit a user defined type for a given engagement
    """

    # User has permission for the engagement
    _db_user, logged_user = referenced.db_user, referenced.db_user.cisco_cco_id

    # Query the user defined type to edit

    udt_query = (
        select(V2UserDefinedTypeORM)
        .where(V2UserDefinedTypeORM.id == payload.id)
        .where(V2UserDefinedTypeORM.dc_engagement_id == payload.dc_engagement_id)
        .where(V2UserDefinedTypeORM.is_deleted == "F")
    )

    db_udt = session.exec(udt_query).one_or_none()
    if not db_udt:
        raise HTTPException(status_code=404, detail="User defined type not found")

    # Check that this field_name and value combination is unique.

    udt_values_query = (
        select(V2UserDefinedTypeORM)
        .where(V2UserDefinedTypeORM.dc_engagement_id == payload.dc_engagement_id)
        .where(V2UserDefinedTypeORM.field_name == db_udt.field_name)
        .where(V2UserDefinedTypeORM.value == payload.value)
    )

    db_existing = session.exec(udt_values_query).one_or_none()

    match db_existing:
        case None:
            db_udt.value = payload.value
            db_udt.updated_by = logged_user
            session.add(db_udt)
            session.commit()
            session.refresh(db_udt)
            return db_udt
        case V2UserDefinedTypeORM(is_deleted="F"):
            raise HTTPException(
                status_code=409,
                detail="Value and field_name combination already exists",
            )
        case V2UserDefinedTypeORM(is_deleted="T"):
            db_existing.is_deleted = "F"
            db_existing.updated_by = logged_user
            db_udt.is_deleted = "T"
            db_udt.updated_by = logged_user
            session.add_all((db_existing, db_udt))
            session.commit()
            session.refresh(db_existing)
            return db_existing
        case _:
            logger.error("Logic Error - Unexpected case")
            raise HTTPException(status_code=500, detail="Unexpected error")
