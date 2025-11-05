import datetime
from typing import Literal

from pydantic import Field

from ... import Model
from . import AMRRSchemaModel, AMRRToolAction, register_schema


class SourceInstanceIdModel(Model):
    source_instance_id: int = Field(..., title="SOURCE INSTANCE ID")
    source_serial_number: str | None = Field(None, title="SOURCE PAK/SERIAL NUMBER")


class SourceSerialNumberModel(Model):
    source_instance_id: int | None = Field(None, title="SOURCE INSTANCE ID")
    source_serial_number: str = Field(..., title="SOURCE PAK/SERIAL NUMBER")


@register_schema
class AMRRDelinkSchema(AMRRSchemaModel):
    tool_action: Literal[AMRRToolAction.delink] = Field(
        AMRRToolAction.delink, title="Tool Action", exclude=True
    )
    source_instance_id: int = Field(..., title="SOURCE INSTANCE ID")
    target_instance_id: int = Field(..., title="TARGET INSTANCE ID")


@register_schema
class AMRRRelinkSchema(AMRRSchemaModel):
    tool_action: Literal[AMRRToolAction.relink] = Field(
        AMRRToolAction.relink, title="Tool Action"
    )
    source_instance_id: int = Field(..., title="SOURCE INSTANCE ID")
    target_instance_id: int = Field(..., title="TARGET INSTANCE ID")


@register_schema
class AMRRSiteMoveSchema(AMRRSchemaModel):
    tool_action: Literal[AMRRToolAction.site_move] = Field(
        AMRRToolAction.site_move, title="Tool Action"
    )
    source_instance_id: int = Field(..., title="SOURCE INSTANCE ID")
    source_site_id: int | None = Field(..., title="SOURCE SITE ID")
    target_site_id: int | None = Field(..., title="TARGET SITE ID")


@register_schema
class AMRRContractMoveSchema(AMRRSchemaModel):
    tool_action: Literal[AMRRToolAction.contract_move] = Field(
        AMRRToolAction.contract_move, title="Tool Action"
    )
    source_instance_id: int | None = Field(..., title="SOURCE INSTANCE ID")
    source_contract_number: int | None = Field(..., title="SOURCE CONTRACT NUMBER")
    source_service_level: str | None = Field(..., title="SOURCE SERVICE LEVEL")
    target_contract_number: int | None = Field(..., title="TARGET CONTRACT NUMBER")


@register_schema
class AMRRAddToContractSchema(AMRRSchemaModel):
    tool_action: Literal[AMRRToolAction.add_to_contract] = Field(
        AMRRToolAction.add_to_contract, title="Tool Action"
    )
    source_instance_id: int | None = Field(..., title="SOURCE INSTANCE ID")
    target_contract_number: int | None = Field(..., title="TARGET CONTRACT NUMBER")
    target_service_level: str | None = Field(..., title="TARGET SERVICE LEVEL")
    start_date: datetime.date | None = Field(..., title="START DATE")
    end_date: datetime.date | None = Field(..., title="END DATE")
    mpo: str | None = Field(..., title="MPO")
    mso: str | None = Field(..., title="MSO")


__all__ = [
    "AMRRAddToContractSchema",
    "AMRRContractMoveSchema",
    "AMRRDelinkSchema",
    "AMRRRelinkSchema",
    "AMRRSiteMoveSchema",
]
