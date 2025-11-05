import datetime
from typing import Annotated, Literal

from pydantic import Field

from ... import Model
from . import CCWRSchemaModel, CCWRToolAction, register_schema


class SourceInstanceIdModel(Model):
    source_instance_id: int = Field(..., title="SOURCE INSTANCE ID")
    source_serial_number: str | None = Field(None, title="SOURCE PAK/SERIAL NUMBER")


class SourceSerialNumberModel(Model):
    source_instance_id: int | None = Field(None, title="SOURCE INSTANCE ID")
    source_serial_number: str = Field(..., title="SOURCE PAK/SERIAL NUMBER")


class TargetInstanceIdModel(Model):
    target_instance_id: int = Field(..., title="TARGET INSTANCE ID")
    target_serial_number: str | None = Field(None, title="TARGET PAK/SERIAL NUMBER")


class TargetSerialNumberModel(Model):
    target_instance_id: int | None = Field(None, title="TARGET INSTANCE ID")
    target_serial_number: str = Field(..., title="TARGET PAK/SERIAL NUMBER")


class AddToContractBase(CCWRSchemaModel):
    tool_action: Literal[CCWRToolAction.add_to_contract] = Field(
        CCWRToolAction.add_to_contract
    )
    quantity: int | None = Field(..., title="QUANTITY")
    target_site_id: str | None = Field(..., title="END CUSTOMER SITE ID")
    target_service_level: str | None = Field(..., title="SERVICE LEVEL")
    start_date: datetime.date | None = Field(..., title="SERVICE BEGIN DATE")
    end_date: datetime.date | None = Field(..., title="SERVICE END DATE")
    target_contract_number: int | None = Field(..., title="TARGET CONTRACT NUMBER")


class AddToContractInstanceModel(
    AddToContractBase,
    SourceInstanceIdModel,
): ...


class AddToContractSerialModel(AddToContractBase, SourceSerialNumberModel): ...


CCWRAddToContractSchemaModel = Annotated[
    AddToContractInstanceModel | AddToContractSerialModel, Field()
]


class CCWRContractMoveBase(CCWRSchemaModel):
    tool_action: Literal[CCWRToolAction.contract_move] = Field(
        CCWRToolAction.contract_move
    )
    source_contract_number: int | None = Field(..., title="SOURCE CONTRACT NUMBER")
    source_service_level: str | None = Field(..., title="SOURCE SERVICE LEVEL")
    target_contract_number: int | None = Field(..., title="TARGET CONTRACT NUMBER")
    reason_code: str | None = Field(..., title="REASON CODE")
    cs_case_number: str | None = Field(..., title="CS CASE NUMBER")


class MoveInstanceModel(CCWRContractMoveBase, SourceInstanceIdModel): ...


class MoveSerialModel(CCWRContractMoveBase, SourceSerialNumberModel): ...


CCWRContractMoveSchemaModel = Annotated[MoveInstanceModel | MoveSerialModel, Field()]


class SiteMoveBase(CCWRSchemaModel):
    tool_action: Literal[CCWRToolAction.site_move] = Field(CCWRToolAction.site_move)
    source_contract_number: int | None = Field(..., title="SOURCE CONTRACT NUMBER")
    source_site_id: str | None = Field(..., title="SOURCE SITE ID")
    source_service_level: str | None = Field(..., title="SOURCE SERVICE LEVEL")
    target_site_id: str | None = Field(..., title="TARGET SITE ID")
    reason_code: str | None = Field(..., title="REASON CODE")
    cs_case_number: str | None = Field(..., title="CS CASE NUMBER")


class CCWRSiteMoveInstanceModel(SiteMoveBase, SourceInstanceIdModel): ...


class CCWRSiteMoveSerialModel(SiteMoveBase, SourceSerialNumberModel): ...


CCWRSiteMoveSchemaModel = Annotated[
    CCWRSiteMoveInstanceModel | CCWRSiteMoveSerialModel, Field()
]


class DoNotRenewBase(CCWRSchemaModel):
    tool_action: Literal[CCWRToolAction.set_do_not_renew_flag] = Field(
        CCWRToolAction.set_do_not_renew_flag
    )
    covered_line_number: str | None = Field(..., title="COVERED LINE NUMBER")
    target_contract_number: int | None = Field(..., title="CONTRACT NUMBER")
    target_service_level: str | None = Field(..., title="SERVICE LEVEL")


class CCWRDoNotRenewInstanceModel(DoNotRenewBase, SourceInstanceIdModel): ...


class CCWRDoNotRenewSerialModel(DoNotRenewBase, SourceSerialNumberModel): ...


CCWRDoNotRenewSchemaModel = Annotated[
    CCWRDoNotRenewInstanceModel | CCWRDoNotRenewSerialModel, Field()
]


class LinkBase(CCWRSchemaModel):
    tool_action: Literal[CCWRToolAction.link_minor_to_major] = Field(
        CCWRToolAction.link_minor_to_major
    )


class LinkInstanceModel(SourceInstanceIdModel, TargetInstanceIdModel, LinkBase): ...


class LinkSerialModel(SourceSerialNumberModel, TargetSerialNumberModel, LinkBase): ...


class LinkSourceInstanceTargetSerialModel(
    SourceInstanceIdModel, TargetSerialNumberModel, LinkBase
): ...


class LinkSourceSerialTargetInstanceModel(
    SourceSerialNumberModel, TargetInstanceIdModel, LinkBase
): ...


CCWRLinkMajorMinorSchemaModel = Annotated[
    LinkInstanceModel
    | LinkSerialModel
    | LinkSourceInstanceTargetSerialModel
    | LinkSourceSerialTargetInstanceModel,
    Field(),
]


class SwapBase(CCWRSchemaModel):
    tool_action: Literal[CCWRToolAction.swap_serial_instance_number] = Field(
        CCWRToolAction.swap_serial_instance_number
    )
    rma_number: str | None = Field(None, title="RMA NUMBER")


class SwapInstanceModel(SwapBase, SourceInstanceIdModel, TargetInstanceIdModel): ...


class SwapSerialModel(SwapBase, SourceSerialNumberModel, TargetSerialNumberModel): ...


class SwapSourceInstanceTargetSerialModel(
    SwapBase, SourceInstanceIdModel, TargetSerialNumberModel
): ...


class SwapSourceSerialTargetInstanceModel(
    SwapBase, SourceSerialNumberModel, TargetInstanceIdModel
): ...


CCWRSwapSerialInstanceSchemaModel = Annotated[
    SwapInstanceModel
    | SwapSerialModel
    | SwapSourceInstanceTargetSerialModel
    | SwapSourceSerialTargetInstanceModel,
    Field(),
]


class UpdateInstallBase(CCWRSchemaModel):
    tool_action: Literal[CCWRToolAction.update_install_base_instance] = Field(
        CCWRToolAction.update_install_base_instance
    )
    target_site_id: str | None = Field(None, title="END CUSTOMER SITE ID")
    instance_status: str | None = Field(None, title="INSTANCE STATUS")


class UpdateInstallInstanceIdModel(UpdateInstallBase, SourceInstanceIdModel): ...


class UpdateInstallSerialNumberModel(UpdateInstallBase, SourceSerialNumberModel): ...


CCWRUpdateInstallInstanceSchemaModel = Annotated[
    UpdateInstallInstanceIdModel | UpdateInstallSerialNumberModel, Field()
]

register_schema(CCWRContractMoveSchemaModel, name="CCWRContractMoveSchemaModel")
register_schema(CCWRSiteMoveSchemaModel, name="CCWRSiteMoveSchemaModel")
register_schema(CCWRDoNotRenewSchemaModel, name="CCWRDoNotRenewSchemaModel")
register_schema(CCWRLinkMajorMinorSchemaModel, name="CCWRLinkMajorMinorSchemaModel")
register_schema(
    CCWRUpdateInstallInstanceSchemaModel, name="CCWRUpdateInstallInstanceSchemaModel"
)
register_schema(CCWRAddToContractSchemaModel, name="CCWRAddToContractSchemaModel")
register_schema(
    CCWRSwapSerialInstanceSchemaModel, name="CCWRSwapSerialInstanceSchemaModel"
)


__all__ = [
    "CCWRAddToContractSchemaModel",
    "CCWRContractMoveSchemaModel",
    "CCWRDoNotRenewSchemaModel",
    "CCWRLinkMajorMinorSchemaModel",
    "CCWRSiteMoveSchemaModel",
    "CCWRSwapSerialInstanceSchemaModel",
    "CCWRUpdateInstallInstanceSchemaModel",
]
