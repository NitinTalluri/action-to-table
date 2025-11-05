import logging
from urllib.parse import urlparse

from fastapi import APIRouter, HTTPException
from starlette.status import HTTP_400_BAD_REQUEST

from api.dependencies import S3ClientDep
from api.v2.models import V2PresignedUrlRequest, V2PresignedUrlResponse

router = APIRouter()

logger = logging.getLogger("api")


@router.post("", response_model=V2PresignedUrlResponse)
def get_presigned_url(s3_request: V2PresignedUrlRequest, s3_client: S3ClientDep):
    """
    Get a pre-signed url for the given s3 file uri that will expire in 1 hour
    """

    # Parse the s3 file uri into bucket and key
    parsed_uri = urlparse(s3_request.url, allow_fragments=False)
    if parsed_uri.scheme != "s3":
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST, detail="Invalid s3 file uri"
        )
    bucket = parsed_uri.netloc
    key = parsed_uri.path.lstrip("/")

    n_hours = 1
    expire_secs = 60 * 60 * n_hours

    presigned_url = s3_client.generate_presigned_url(
        ClientMethod="get_object",
        Params={"Bucket": bucket, "Key": key},
        ExpiresIn=expire_secs,
    )

    logger.info(
        "Generated presigned url for %s that will expire in %d seconds",
        s3_request.url,
        expire_secs,
    )

    return V2PresignedUrlResponse(
        requested_url=s3_request.url, url=presigned_url, expires_secs=expire_secs
    )
