from typing import TYPE_CHECKING

from typing_extensions import Unpack

from .exceptions import ServiceException

if TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client
    from mypy_boto3_s3.type_defs import PutObjectRequestTypeDef


class S3Mixin:
    def __init__(self, s3_client: "S3Client"):
        self.s3_client = s3_client

    def upload_to_s3(
        self,
        bucket: str,
        key: str,
        body: bytes,
        **kwargs: Unpack["PutObjectRequestTypeDef"],
    ):
        try:
            params = {
                "Bucket": bucket,
                "Key": key,
                "Body": body,
                **kwargs,
            }
            return self.s3_client.put_object(**params)
        except Exception as e:
            raise ServiceException(f"Error uploading to S3: {e}", 500) from e


__all__ = ["S3Mixin"]
