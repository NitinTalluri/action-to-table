import logging
from typing import (
    TYPE_CHECKING,
    Annotated,
    Callable,
    Optional,
    TypeVar,
    Union,
)
from urllib.parse import urlparse

from fastapi import Depends

from . import GetSettingsDep  # noqa

if TYPE_CHECKING:
    from mypy_boto3_cognito_idp import CognitoIdentityProviderClient
    from mypy_boto3_cognito_idp.type_defs import UserTypeTypeDef
    from mypy_boto3_s3 import S3Client

    from api.v2.models import DocumentationLinkResponseModel
    from api.v2.orm import DocumentationLinks


T = TypeVar(
    "T",
    "DocumentationLinks",
    "DocumentationLinkResponseModel",
    list["DocumentationLinks"],
    list["DocumentationLinkResponseModel"],
)
V = TypeVar(
    "V", "DocumentationLinkResponseModel", list["DocumentationLinkResponseModel"]
)


logger = logging.getLogger("api")


async def get_s3_client(settings: GetSettingsDep) -> "S3Client":
    """
    Get a boto3 client
    """
    import boto3

    session = boto3.session.Session(
        region_name=settings.aws_region,
    )
    s3 = session.client("s3")
    return s3


async def get_idp_client(settings: GetSettingsDep) -> "CognitoIdentityProviderClient":
    """
    Get a cognito-idp boto3 client
    """
    import boto3

    session = boto3.session.Session(
        region_name=settings.aws_region,
    )
    client = session.client("cognito-idp")
    return client


S3ClientDep = Annotated["S3Client", Depends(get_s3_client)]
IdpClientDep = Annotated["CognitoIdentityProviderClient", Depends(get_idp_client)]


def cognito_group_getter(client: IdpClientDep, settings: GetSettingsDep):
    """
    Creates a factory to get users in one or more cognito groups
    """

    def get_email_from_attributes(user: "UserTypeTypeDef") -> Optional[str]:
        matched = next(
            (attr for attr in user["Attributes"] if attr["Name"] == "email"), None
        )
        if matched:
            return matched["Value"]
        try:
            return user["Username"].split("_")[1]
        except:
            return None

    def get_users_in_groups(*group_names: str) -> set[str]:
        paginator = client.get_paginator("list_users_in_group")
        users = set()
        for group_name in group_names:
            response = paginator.paginate(
                UserPoolId=settings.user_pool_id, GroupName=group_name
            )
            flat_response: list[UserTypeTypeDef] = [
                user for page in response for user in page["Users"]
            ]
            emails = [get_email_from_attributes(user) for user in flat_response]
            users.update([email for email in emails if email is not None])
        return users

    return get_users_in_groups


GroupGetterDep = Annotated[callable, Depends(cognito_group_getter)]


class S3Presigner:
    def __init__(self, expire_secs: int = 86400):
        self.expire_secs = expire_secs
        self.s3_client = None

    def __call__(self, s3_client: S3ClientDep):
        self.s3_client = s3_client
        return self

    def get_presigned_url(self, bucket: str, key: str) -> str:
        if self.s3_client is None:
            raise ValueError("S3 client not initialized")
        presigned_url = self.s3_client.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=self.expire_secs,
        )
        return presigned_url


class S3DocumentationPresigner:
    def __init__(self, expire_secs: int = 86400):
        self.expire_secs = expire_secs

    def __call__(self, s3_client: S3ClientDep):
        def get_presigned_url(url: str) -> str:
            parsed_uri = urlparse(url, allow_fragments=False)
            if parsed_uri.scheme != "s3":
                logger.warning("Invalid s3 file uri: %s, returning as is", url)
                return url
            bucket = parsed_uri.netloc
            key = parsed_uri.path.lstrip("/")
            presigned_url = s3_client.generate_presigned_url(
                ClientMethod="get_object",
                Params={"Bucket": bucket, "Key": key},
                ExpiresIn=self.expire_secs,
            )
            return presigned_url

        def presign_doc_model(
            model: Union["DocumentationLinks", "DocumentationLinkResponseModel"],
        ) -> "DocumentationLinkResponseModel":
            from api.v2.models import DocumentationLinkResponseModel
            from api.v2.orm import DocumentationLinks

            match model:
                case DocumentationLinks(doc_url=str(doc_url)) if doc_url.startswith(
                    "s3://"
                ):
                    presigned_url = get_presigned_url(doc_url)
                    return DocumentationLinkResponseModel(
                        doc_url=presigned_url,
                        doc_desc=model.doc_desc,
                        doc_type=model.doc_type,
                        doc_id=model.doc_id,
                        ui_enum=model.ui_enum,
                        position=model.position,
                    )
                case DocumentationLinks():
                    return DocumentationLinkResponseModel.from_orm(model)
                case DocumentationLinkResponseModel(doc_url=str(doc_url)) if (
                    doc_url.startswith("s3://")
                ):
                    presigned_url = get_presigned_url(doc_url)
                    return DocumentationLinkResponseModel(
                        doc_url=presigned_url,
                        doc_desc=model.doc_desc,
                        doc_type=model.doc_type,
                        doc_id=model.doc_id,
                        ui_enum=model.ui_enum,
                        position=model.position,
                    )
                case DocumentationLinkResponseModel():
                    return model
                case _:
                    raise ValueError(f"Invalid model type: {model}")

        def presigner(doc: "T") -> "V":
            match doc:
                case list(iter_docs):
                    return [presign_doc_model(d) for d in iter_docs]
                case _:
                    return presign_doc_model(doc)

        return presigner


DocumentationPresigner = S3DocumentationPresigner(expire_secs=86400)
StaticPresigner = S3Presigner(expire_secs=86400)
PresignedDocsDep = Annotated[Callable[["T"], "V"], Depends(DocumentationPresigner)]
S3PresignerDep = Annotated[S3Presigner, Depends(StaticPresigner)]


__all__ = [
    "GroupGetterDep",
    "IdpClientDep",
    "PresignedDocsDep",
    "S3ClientDep",
    "S3PresignerDep",
]
