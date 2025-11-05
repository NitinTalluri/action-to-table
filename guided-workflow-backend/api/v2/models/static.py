from . import Model


class V2StaticPresignedUrlResponse(Model):
    url: str
    expires_secs: int
