from pydantic.v1 import Field

from .. import Model


class V2PresignedUrlRequest(Model):
    url: str = Field(
        ...,
        description="The s3 file uri for which to generate a pre-signed url",
        example="s3://dc-serial-resolution/dev/excel/211475.xlsx",
    )


class V2PresignedUrlResponse(Model):
    requested_url: str
    url: str
    expires_secs: int
