from typing import Literal, Protocol, TypedDict, Union

from pydantic import Field

from api.v2.models import Model, StrEnum

THistoricalToolActionLiteral = Literal["old_macd"]


class ToolName(StrEnum):
    acat = "acat"
    amrr = "amrr"
    ccwr = "ccwr"


TToolNameLiteral = Literal["acat", "amrr", "ccwr", "historical"]
TToolName = ToolName | TToolNameLiteral


class AMRRToolAction(StrEnum):
    delink = "delink"
    relink = "relink"
    site_move = "site_move"
    contract_move = "contract_move"
    add_to_contract = "add_to_contract"


TAMRRToolActionLiteral = Literal[
    "delink", "relink", "site_move", "contract_move", "add_to_contract"
]
TAMRRToolAction = AMRRToolAction | TAMRRToolActionLiteral


class CCWRToolAction(StrEnum):
    add_to_contract = "add_to_contract"
    contract_move = "contract_move"
    site_move = "site_move"
    set_do_not_renew_flag = "set_do_not_renew_flag"
    link_minor_to_major = "link_minor_to_major"
    update_install_base_instance = "update_install_base_instance"
    swap_serial_instance_number = "swap_serial_instance_number"


TCCWRToolActionLiteral = Literal[
    "add_to_contract",
    "contract_move",
    "site_move",
    "set_do_not_renew_flag",
    "link_minor_to_major",
    "update_install_base_instance",
    "swap_serial_instance_number",
]
TCCWRToolAction = CCWRToolAction | TCCWRToolActionLiteral


class ACATToolAction(StrEnum):
    add_to_contract = "add_to_contract"
    termination = "termination"
    decommission = "decommission"


TACATToolActionLiteral = Literal["add_to_contract", "termination", "decommission"]
TACATToolAction = ACATToolAction | TACATToolActionLiteral


TToolAction = TACATToolAction | TAMRRToolAction | TCCWRToolAction
TToolActionLiteral = Union[
    THistoricalToolActionLiteral,
    TACATToolActionLiteral,
    TAMRRToolActionLiteral,
    TCCWRToolActionLiteral,
]

TRegistryKey = tuple[TToolNameLiteral, TToolActionLiteral]


class SchemaModelBase(Model):
    tool_name: TToolNameLiteral = Field(..., title="Tool Name")
    tool_action: TToolActionLiteral = Field(..., title="Tool Action")

    @property
    def schema_key(self) -> TRegistryKey:
        return self.tool_name, self.tool_action


class ACATSchemaModel(SchemaModelBase):
    tool_name: Literal[ToolName.acat] = Field(ToolName.acat.value, title="Tool Name")
    tool_action: ACATToolAction


class AMRRSchemaModel(SchemaModelBase):
    tool_name: Literal[ToolName.amrr] = Field(ToolName.amrr.value, title="Tool Name")
    tool_action: AMRRToolAction


class CCWRSchemaModel(SchemaModelBase):
    tool_name: Literal[ToolName.ccwr] = Field(ToolName.ccwr.value, title="Tool Name")
    tool_action: CCWRToolAction


class FieldSchema(TypedDict, total=False):
    title: str
    description: str | None
    default: str | int | float | bool | None
    enum: list[str]
    type: Literal["string", "number", "boolean", "integer"]
    format: Literal["date", "date-time", "regex"]
    json_schema_extra: dict


TFieldProperty = dict[str, FieldSchema]


class ModelSchema(TypedDict, total=False):
    title: str
    type: Literal["object"]
    properties: dict[str, TFieldProperty]
    required: list[str]


class DiscrimatorSchema(TypedDict):
    propertyName: str
    mapping: dict[str, str]


TRef = Literal["$ref"]

TOneOfSchema = list[dict[TRef, str]]


class UnionModelSchema(TypedDict):
    title: str
    discriminator: DiscrimatorSchema
    oneOf: TOneOfSchema
    definitions: dict[str, ModelSchema]


class DiscriminatedUnionModelSchema(UnionModelSchema):
    discriminator: DiscrimatorSchema


TRegistryExport = list[ModelSchema | UnionModelSchema | DiscriminatedUnionModelSchema]


__all__ = [
    "ACATSchemaModel",
    "AMRRSchemaModel",
    "CCWRSchemaModel",
    "DiscriminatedUnionModelSchema",
    "SchemaModelBase",
    "TACATToolAction",
    "TACATToolActionLiteral",
    "TAMRRToolActionLiteral",
    "TCCWRToolAction",
    "TCCWRToolActionLiteral",
    "TRegistryExport",
    "TToolActionLiteral",
    "TToolName",
    "TToolNameLiteral",
    "ToolName",
]
