import datetime
from typing import Annotated, Literal

from pydantic import Field

from ... import Model
from . import ACATSchemaModel, ACATToolAction, register_schema


class ACATFieldsBase(Model):
    target_contract_number: int | None = Field(
        default=None, title="Target Contract Number"
    )
    target_service_level: str | None = Field(default=None, title="Target Service Level")
    start_date: datetime.date | None = Field(default=None, title="Begin Date")
    end_date: datetime.date | None = Field(default=None, title="Termination Date")
    source_serial_number: str | None = Field(
        default=None, title="Serial Number/PAK Number"
    )
    product_id: str | None = Field(default=None, title="Product ID")
    target_site_id: str | None = Field(default=None, title="Target Site ID")
    source_instance_id: int | None = Field(default=None, title="Instance Number")
    justification_reason: str | None = Field(default=None, title="Justification Reason")
    error_message: str | None = Field(default=None, title="Error Message")


class SourceInstanceIdModel(ACATFieldsBase):
    source_instance_id: int = Field(..., title="Instance Number")


class SourceSerialNumberModel(ACATFieldsBase):
    source_serial_number: str = Field(..., title="Serial Number/PAK Number")


class AddToContractBase(ACATSchemaModel):
    tool_action: Literal[ACATToolAction.add_to_contract] = Field(
        ACATToolAction.add_to_contract, title="Tool Action"
    )
    target_contract_number: int | None = Field(
        default=None, title="Target Contract Number"
    )
    target_service_level: str | None = Field(default=None, title="Target Service Level")
    start_date: datetime.date | None = Field(default=None, title="Begin Date")
    end_date: datetime.date | None = Field(default=None, title="Termination Date")
    target_site_id: str | None = Field(default=None, title="Target Site ID")


class AddToContractInstanceModel(AddToContractBase, SourceInstanceIdModel): ...


class AddToContractSerialModel(AddToContractBase, SourceSerialNumberModel): ...


ACATAddToContractSchema = Annotated[
    AddToContractInstanceModel | AddToContractSerialModel, Field()
]

register_schema(ACATAddToContractSchema, "ACATAddToContractSchema")


class TerminationBase(ACATSchemaModel):
    tool_action: Literal[ACATToolAction.termination] = Field(
        ACATToolAction.termination, title="Tool Action"
    )
    target_contract_number: int | None = Field(
        default=None, title="Target Contract Number"
    )
    target_service_level: str | None = Field(default=None, title="Target Service Level")
    start_date: datetime.date | None = Field(default=None, title="Begin Date")
    end_date: datetime.date | None = Field(default=None, title="Termination Date")
    product_id: str | None = Field(default=None, title="Product ID")
    target_site_id: str | None = Field(default=None, title="Target Site ID")
    justification_reason: str | None = Field(default=None, title="Justification Reason")


class TerminationInstanceModel(TerminationBase, SourceInstanceIdModel): ...


class TerminationSerialModel(TerminationBase, SourceSerialNumberModel): ...


ACATTerminationSchema = Annotated[
    TerminationInstanceModel | TerminationSerialModel, Field()
]
register_schema(ACATTerminationSchema, "ACATTerminationSchema")


class DecommissionBase(ACATSchemaModel):
    tool_action: Literal[ACATToolAction.decommission] = Field(
        ACATToolAction.decommission, title="Tool Action"
    )
    target_contract_number: int | None = Field(
        default=None, title="Target Contract Number"
    )
    target_service_level: str | None = Field(default=None, title="Target Service Level")
    start_date: datetime.date | None = Field(default=None, title="Begin Date")
    end_date: datetime.date | None = Field(default=None, title="Termination Date")
    product_id: str | None = Field(default=None, title="Product ID")
    target_site_id: str | None = Field(default=None, title="Target Site ID")
    justification_reason: str | None = Field(default=None, title="Justification Reason")


class DecommissionInstanceModel(DecommissionBase, SourceInstanceIdModel): ...


class DecommissionSerialModel(DecommissionBase, SourceSerialNumberModel): ...


ACATDecommissionSchema = Annotated[
    DecommissionInstanceModel | DecommissionSerialModel, Field()
]

register_schema(ACATDecommissionSchema, "ACATDecommissionSchema")


__all__ = [
    "ACATAddToContractSchema",
    "ACATDecommissionSchema",
    "ACATTerminationSchema",
]
