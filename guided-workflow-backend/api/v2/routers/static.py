import logging

from fastapi import APIRouter

from api.dependencies import (
    GetSettingsDep,
    GetUserDep,
    PresignedDocsDep,
    S3ClientDep,
    S3PresignerDep,
)
from api.v2.models.static import V2StaticPresignedUrlResponse

router = APIRouter()

logger = logging.getLogger("api")


@router.get("/html", response_model=V2StaticPresignedUrlResponse)
def get_static_html_presigned_url(
    settings: GetSettingsDep,
    s3_presigner: S3PresignerDep,
):
    """
    Get a pre-signed URL for a static HTML file that will expire in 12 hours.
    Currently used ad-hoc to support sharing development teams static_view.html
    """

    static_bucket = settings.docs_bucket
    static_key = settings.static_html_key

    presigned_url = s3_presigner.get_presigned_url(bucket=static_bucket, key=static_key)

    return V2StaticPresignedUrlResponse(
        url=presigned_url, expires_secs=s3_presigner.expire_secs
    )
