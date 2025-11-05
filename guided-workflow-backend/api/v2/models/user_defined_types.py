from pydantic.v1 import Field

from . import Model


class V2UserDefinedType(Model):
    id: int
    value: str
    field_name: str
    dc_engagement_id: int


class V2UserDefinedTypeCreate(Model):
    value: str = Field(
        ...,
        description="The 'string' value of the user defined type",
        example="My Important Value",
    )
    field_name: str = Field(
        ...,
        description="The field this value is associated with",
        example="collector-file",
    )
    dc_engagement_id: int = Field(
        ..., description="The engagement id this value is associated with", example=727
    )


class V2UserDefinedTypeDelete(Model):
    id: int = Field(
        ..., description="The id of the user defined type to delete", example=1
    )
    dc_engagement_id: int = Field(
        ..., description="The engagement id this value is associated with", example=727
    )


class V2UserDefinedTypeEdit(Model):
    id: int = Field(
        ..., description="The id of the user defined type to edit", example=1
    )
    dc_engagement_id: int = Field(
        ..., description="The engagement id this value is associated with", example=727
    )
    value: str = Field(
        ...,
        description="The 'string' value of the user defined type",
        example="My Important Value",
    )
