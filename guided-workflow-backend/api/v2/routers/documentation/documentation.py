from io import BytesIO
from logging import getLogger
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile
from pydantic.v1 import Json
from sqlmodel import select
from starlette.datastructures import UploadFile as StarletteUploadFile
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_500_INTERNAL_SERVER_ERROR

from api.dependencies import (
    GetSessionDep,
    GetSettingsDep,
    GetUserDep,
    PresignedDocsDep,
    S3ClientDep,
    is_sme_or_admin,
)
from api.v2.models import (
    DocumentationLinkCreate,
    DocumentationLinkResponseModel,
    DocumentationLinkUpdate,
)
from api.v2.orm import DocumentationLinks
from api.v2.queries import (
    create_position_insert_statement,
    create_position_update_statement,
    query_documentation_append_position,
)

logger = getLogger(__name__)

router = APIRouter()


@router.post(
    "",
    response_model=DocumentationLinkResponseModel,
    dependencies=[Depends(is_sme_or_admin)],
)
async def create_documentation_link(
    session: GetSessionDep,
    db_user: GetUserDep,
    presigner: PresignedDocsDep,
    s3_client: S3ClientDep,
    settings: GetSettingsDep,
    payload: Annotated[Json[DocumentationLinkCreate], Form()],
    file: Optional[UploadFile] = None,
):
    """
    Create a new documentation link

    ### Uploading a file

    If uploading a file, the doc_url should be None. The file will be uploaded to S3
    and the will be set to the S3 URL. The 'upload' field should be set to True.

    ### Creating a link

    If a resource is already hosted elsewhere, the doc_url should be set to the URL of the resource.
    The 'upload' field should be set to False.



    """

    payload = payload.__root__
    is_upload = payload.upload

    db_doc_link = DocumentationLinks(
        **payload.dict(exclude={"upload"}), created_by=db_user.cisco_cco_id
    )

    match is_upload, file:
        case True, None:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST, detail="No file provided"
            )
        case True, UploadFile() | StarletteUploadFile():
            file_name = file.filename
            contents = await file.read()
            await file.close()
            io = BytesIO(contents)
            io.seek(0)

            file_key = f"{settings.env!s}/{file_name}"
            file_uri = f"s3://{settings.docs_bucket}/{file_key}"
            logger.info("Uploading documentation file to %s", file_uri)
            try:
                s3_client.upload_fileobj(io, settings.docs_bucket, file_key)
            except Exception as e:
                logger.exception("Failed to documentation file to %s", file_uri)
                raise HTTPException(
                    status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to upload documentation file",
                ) from e
            db_doc_link.doc_url = file_uri

        case False, UploadFile():
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail="File provided but 'upload' is set to False",
            )
        case _:
            ...

    if db_doc_link.position is None:
        position_query = query_documentation_append_position(payload.ui_enum)
        db_doc_link.position = session.exec(position_query).scalar_one_or_none() or 0
        session.add(db_doc_link)
        session.commit()
        session.refresh(db_doc_link)
        return presigner(db_doc_link)

    # We need to shift positions around
    update_positions_stmt = create_position_insert_statement(
        payload.ui_enum, payload.position, db_user.cisco_cco_id
    )

    session.exec(update_positions_stmt)
    session.add(db_doc_link)
    session.commit()
    session.refresh(db_doc_link)
    return presigner(db_doc_link)


@router.get("", response_model=list[DocumentationLinkResponseModel])
def query_documentation_links(
    session: GetSessionDep,
    presigner: PresignedDocsDep,
    ui_enum: Optional[str] = None,
    doc_type: Optional[str] = None,
    doc_url: Optional[str] = None,
):
    """Get all documentation links, with optional filtering"""
    query_base = select(DocumentationLinks).where(DocumentationLinks.is_deleted == "F")
    if ui_enum:
        query_base = query_base.where(DocumentationLinks.ui_enum == ui_enum)
    if doc_type:
        query_base = query_base.where(DocumentationLinks.doc_type == doc_type)
    if doc_url:
        query_base = query_base.where(DocumentationLinks.doc_url == doc_url)
    query = query_base
    results = session.exec(query).all()
    presigned_result = presigner(results)
    return presigned_result


@router.get("/{doc_id}", response_model=DocumentationLinkResponseModel)
def get_documentation_link(
    doc_id: int, session: GetSessionDep, presigner: PresignedDocsDep
):
    """Get a single documentation link by ID"""
    db_documentation_link = session.exec(
        select(DocumentationLinks)
        .where(DocumentationLinks.doc_id == doc_id)
        .where(DocumentationLinks.is_deleted == "F")
    ).one()
    return presigner(db_documentation_link)


@router.patch(
    "/{doc_id}",
    response_model=DocumentationLinkResponseModel,
    dependencies=[Depends(is_sme_or_admin)],
)
def update_documentation_link(
    doc_id: int,
    payload: DocumentationLinkUpdate,
    db_user: GetUserDep,
    session: GetSessionDep,
    presigner: PresignedDocsDep,
):
    db_documentation_link = session.exec(
        select(DocumentationLinks)
        .where(DocumentationLinks.doc_id == doc_id)
        .where(DocumentationLinks.is_deleted == "F")
    ).one()

    # Remove any unset fields
    data = payload.dict(exclude_unset=True, exclude_none=True)
    if not data:
        return db_documentation_link

    new_position = data.pop("position", None)

    if db_documentation_link.position != new_position and new_position is not None:
        stmt = create_position_update_statement(
            wf_enum=db_documentation_link.ui_enum,
            prev_position=db_documentation_link.position,
            new_position=payload.__root__.position,
            cisco_cco_id=db_user.cisco_cco_id,
        )
        session.exec(stmt)
        session.commit()
        session.refresh(db_documentation_link)

    for key, value in data.items():
        setattr(db_documentation_link, key, value)
    db_documentation_link.updated_by = db_user.cisco_cco_id
    session.commit()
    session.refresh(db_documentation_link)
    return presigner(db_documentation_link)


@router.delete(
    "/{doc_id}",
    response_model=DocumentationLinkResponseModel,
    dependencies=[Depends(is_sme_or_admin)],
)
def delete_documentation_link(doc_id: int, session: GetSessionDep, db_user: GetUserDep):
    db_documentation_link = session.exec(
        select(DocumentationLinks)
        .where(DocumentationLinks.doc_id == doc_id)
        .where(DocumentationLinks.is_deleted == "F")
    ).one()
    db_documentation_link.soft_delete(db_user.cisco_cco_id, session)
    return db_documentation_link
