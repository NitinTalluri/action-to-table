from datetime import date
from enum import Enum
from typing import Annotated, Literal, Optional, Union

from pydantic.v1 import Field

from .. import Model


class SchemaType(str, Enum):
    instance_id_fields = "instance_id_fields"
    instance_id_full = "instance_id_full"
    serial_number_fields = "serial_number_fields"
    serial_number_full = "serial_number_full"

    def __str__(self) -> str:
        return str.__str__(self)


class AddressFull(Model):
    full_address: Optional[str] = Field(None, description="Full Address")


class AddressFields(Model):
    street_address: Optional[str] = Field(None, description="Street Address")
    city: Optional[str] = Field(None, description="City")
    state: Optional[str] = Field(None, description="State")
    country: Optional[str] = Field(None, description="Country")


class InstanceId(Model):
    instance_id: Optional[str] = Field(None, description="Instance Id")
    serial_number: Literal[None] = Field(None, description="Serial Number")


class SerialNumber(Model):
    instance_id: Literal[None] = Field(None, description="Instance Id")
    serial_number: Optional[str] = Field(None, description="Serial Number")


class BaseCustomerRow(Model):
    host_name: Optional[str] = Field(None, description="Host name")
    ip_address: Optional[str] = Field(None, description="IP Address")


class InstanceIdFields(BaseCustomerRow, InstanceId, AddressFields): ...


class InstanceIdFull(BaseCustomerRow, InstanceId, AddressFull): ...


class SerialNumberFields(BaseCustomerRow, SerialNumber, AddressFields): ...


class SerialNumberFull(BaseCustomerRow, SerialNumber, AddressFull): ...


class UploadBase(Model):
    file_name_id: int = Field(None, description="The Id of the User Defined Type")
    effective_date: date = Field(None, description="Effective Date")
    source: Optional[str] = Field(None, description="Source")
    note: Optional[str] = Field(None, description="Notes")
    dc_engagement_id: int = Field(..., description="Engagement ID")


class UploadInstanceIdFields(UploadBase):
    schema_type: Literal[SchemaType.instance_id_fields] = Field(
        ..., description="Schema Type", example="instance_id_fields"
    )


class UploadInstanceIdFull(UploadBase):
    schema_type: Literal[SchemaType.instance_id_full] = Field(
        ..., description="Schema Type", example="instance_id_full"
    )


class UploadSerialNumberFields(UploadBase):
    schema_type: Literal[SchemaType.serial_number_fields] = Field(
        ..., description="Schema Type", example="serial_number_fields"
    )


class UploadSerialNumberFull(UploadBase):
    schema_type: Literal[SchemaType.serial_number_full] = Field(
        ..., description="Schema Type", example="serial_number_full"
    )


V2CustomerFileUpload = Annotated[
    Union[
        UploadInstanceIdFields,
        UploadInstanceIdFull,
        UploadSerialNumberFields,
        UploadSerialNumberFull,
    ],
    Field(discriminator="schema_type"),
]


TCustomerRowModel = (
    list[InstanceIdFields]
    | list[InstanceIdFull]
    | list[SerialNumberFields]
    | list[SerialNumberFull]
)


def get_customer_row_model_for_schema_type(
    schema_type: SchemaType,
) -> type[InstanceIdFields | InstanceIdFull | SerialNumberFields | SerialNumberFull]:
    schema_type_inner = SchemaType(schema_type)
    mapping = {
        SchemaType.instance_id_fields: InstanceIdFields,
        SchemaType.instance_id_full: InstanceIdFull,
        SchemaType.serial_number_fields: SerialNumberFields,
        SchemaType.serial_number_full: SerialNumberFull,
    }
    return mapping[schema_type_inner]
