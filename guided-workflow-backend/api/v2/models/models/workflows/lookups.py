from datetime import date
from enum import Enum
from typing import Annotated, Literal, Union

from pydantic.v1 import Field, conlist, constr, validator

from .. import Model


class UploadType(str, Enum):
    serial_number = "serial_number"
    instance_id = "instance_id"

    def __str__(self) -> str:
        return str.__str__(self)


class V2SNIFReportInstances(Model):
    ids: list[int] = Field(
        ..., description="List of instance ids", example=[123456, 123457]
    )
    engagement_id: int = Field(..., description="Engagement id", example=94)
    id_type: Literal[UploadType.instance_id] = Field(
        ..., description="Type of id", example="instance_id"
    )


class V2SNIFReportSerials(Model):
    ids: list[constr(strip_whitespace=True)] = Field(
        ..., description="List of serial numbers", example=["AXB123456", "123457AXB"]
    )
    engagement_id: int = Field(..., description="Engagement id", example=94)
    id_type: Literal[UploadType.serial_number] = Field(
        ..., description="Type of id", example="serial_number"
    )


class V2SNIFReportUpload(Model):
    __root__: Annotated[
        Union[V2SNIFReportInstances, V2SNIFReportSerials],
        Field(discriminator="id_type"),
    ]

    class Config:
        schema_extra = {
            "examples": [
                {
                    "ids": [123456, 123459],
                    "engagement_id": 94,
                    "id_type": "instance_id",
                },
                {
                    "ids": ["AXB123456", "123457AXB"],
                    "engagement_id": 94,
                    "id_type": "serial_number",
                },
            ]
        }


class V2SiteReportUpload(Model):
    engagement_id: int = Field(..., description="Engagement id", example=94)


class V2TagHistoryReportInstances(Model):
    dc_engagement_id: int = Field(
        ..., description="Engagement id", example=94, alias="engagement_id"
    )
    id_type: Literal[UploadType.instance_id] = Field(
        UploadType.instance_id,
        description="Type of id",
        example="instance_id",
        const=True,
    )
    tagset_ids: list[int] = Field(
        ..., description="List of tagset ids", example=[123, 456]
    )
    from_date: date = Field(
        ...,
        description="Query history between this date and present",
        example="2024-01-01",
    )


class V2TagHistoryReportSerials(Model):
    dc_engagement_id: int = Field(
        ..., description="Engagement id", example=94, alias="engagement_id"
    )
    id_type: Literal[UploadType.serial_number] = Field(
        UploadType.serial_number,
        description="Type of id",
        example="serial_number",
        const=True,
    )
    tagset_ids: list[int] = Field(
        ..., description="List of tagset ids", example=[123, 456]
    )
    from_date: date = Field(
        ...,
        description="Query history between this date and present",
        example="2024-01-01",
    )


V2TagHistoryReportUpload = Annotated[
    Union[V2TagHistoryReportInstances, V2TagHistoryReportSerials],
    Field(discriminator="id_type"),
]


class V2HostNameSiteMovesModel(Model):
    engagement_id: int = Field(..., description="Engagement id", example=94)


class V2AcatDiscoveryModel(Model):
    engagement_id: int = Field(..., description="Engagement id", example=94)


class V2HostNameRelinkModel(Model):
    engagement_id: int = Field(..., description="Engagement id", example=94)
