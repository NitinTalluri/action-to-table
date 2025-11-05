from collections import defaultdict
from typing import TYPE_CHECKING, Optional

from fastapi import APIRouter
from sqlalchemy import func, literal, literal_column, type_coerce
from sqlmodel import select, union_all

from api.dependencies import GetSessionDep
from api.v2.models import V2TableTypeMapping
from api.v2.orm import (
    RootCauseType,
    SDPAnchorDate,
    SDPAnchorDateIterator,
    SDPTaskCompletionReason,
    V2AssetMgtType,
    V2BookingContractType,
    V2BookingOverrideReason,
    V2BookingsUserRole,
    V2BuyingPrograms,
    V2ContractType,
    V2DisengagementReason,
    V2EngagementSFCType,
    V2MonitorType,
    V2PricingModel,
    V2SalesLevel,
    V2ServicePlans,
    V2StakeholderType,
    V2Theater,
    V2WfDeferSignoffReason,
    V2WfSignoffEvent,
    V2WfSignoffIdentity,
    V2WfSignoffMethod,
)
from api.v2.orm.json_varchar import JSONVarchar

if TYPE_CHECKING:
    from typing import Any, Type

    from api.v2.orm.base import V2MetadataBase

router = APIRouter()


@router.get("", response_model=list[V2TableTypeMapping])
def v2_get_dc_types(session: GetSessionDep):
    """Get Ids for common types"""

    # To get the result set, we're going to union all the select statements
    # Then, create a dictionary of the results where the key is the table name and the value is the result set

    # Select all the types
    dc_models = (
        (
            V2AssetMgtType,
            V2AssetMgtType.am_type_id,
            V2AssetMgtType.asset_management_type,
            V2AssetMgtType.is_deleted,
            literal_column("null").label("extra"),
        ),
        (
            V2MonitorType,
            V2MonitorType.monitor_type_id,
            V2MonitorType.monitor_reason,
            V2MonitorType.is_deleted,
            literal_column("null").label("extra"),
        ),
        (
            V2ContractType,
            V2ContractType.contract_type_id,
            V2ContractType.service_contract_type,
            V2ContractType.is_deleted,
            literal_column("null").label("extra"),
        ),
        (
            V2EngagementSFCType,
            V2EngagementSFCType.sfc_type_id,
            V2EngagementSFCType.sfc_agreement_type,
            V2EngagementSFCType.is_deleted,
            literal_column("null").label("extra"),
        ),
        (
            V2StakeholderType,
            V2StakeholderType.stakeholder_type_id,
            V2StakeholderType.stakeholder_type,
            V2StakeholderType.is_deleted,
            literal_column("null").label("extra"),
        ),
        (
            V2ServicePlans,
            V2ServicePlans.service_type_id,
            V2ServicePlans.sold_as_service_name,
            V2ServicePlans.is_deleted,
            literal_column("null").label("extra"),
        ),
        (
            V2Theater,
            V2Theater.theater_id,
            V2Theater.theater_name,
            V2Theater.is_deleted,
            literal_column("null").label("extra"),
        ),
        (
            V2PricingModel,
            V2PricingModel.pricing_type_id,
            V2PricingModel.pricing_model_name,
            V2PricingModel.is_deleted,
            literal_column("null").label("extra"),
        ),
        (
            V2BuyingPrograms,
            V2BuyingPrograms.buying_program_type_id,
            V2BuyingPrograms.buying_program_name,
            V2BuyingPrograms.is_deleted,
            V2BuyingPrograms.extra,
        ),
        (
            V2BookingsUserRole,
            V2BookingsUserRole.bookings_role_id,
            V2BookingsUserRole.bookings_role,
            func.iff(
                V2BookingsUserRole.bookings_role == "UNKNOWN",
                "T",
                V2BookingsUserRole.is_deleted,
            ),
            literal_column("null").label("extra"),
        ),
        (
            V2DisengagementReason,
            V2DisengagementReason.disengagement_reason_id,
            V2DisengagementReason.disengagement_reason,
            V2DisengagementReason.is_deleted,
            literal_column("null").label("extra"),
        ),
        (
            V2WfSignoffMethod,
            V2WfSignoffMethod.signoff_method_id,
            V2WfSignoffMethod.signoff_method,
            V2WfSignoffMethod.is_deleted,
            literal_column("null").label("extra"),
        ),
        (
            V2WfSignoffIdentity,
            V2WfSignoffIdentity.sign_off_identity_id,
            V2WfSignoffIdentity.sign_off_identity,
            func.iff(
                V2WfSignoffIdentity.sign_off_identity == "UNKNOWN",
                "T",
                V2WfSignoffIdentity.is_deleted,
            ).label("is_deleted"),
            literal_column("null").label("extra"),
        ),
        (
            V2WfDeferSignoffReason,
            V2WfDeferSignoffReason.defer_signoff_reason_id,
            V2WfDeferSignoffReason.defer_signoff_reason,
            V2WfDeferSignoffReason.is_deleted,
            literal_column("null").label("extra"),
        ),
        (
            V2WfSignoffEvent,
            V2WfSignoffEvent.signoff_event_id,
            V2WfSignoffEvent.signoff_event,
            V2WfSignoffEvent.is_deleted,
            literal_column("null").label("extra"),
        ),
        (
            RootCauseType,
            RootCauseType.root_cause_id,
            RootCauseType.root_cause,
            RootCauseType.is_deleted,
            literal_column("null").label("extra"),
        ),
        (
            V2BookingContractType,
            V2BookingContractType.id,
            V2BookingContractType.value,
            V2BookingContractType.is_deleted,
            V2BookingContractType.extra,
        ),
        (
            SDPAnchorDate,
            SDPAnchorDate.anchor_date_id,
            SDPAnchorDate.anchor_date_name,
            SDPAnchorDate.is_deleted,
            literal_column("null").label("extra"),
        ),
        (
            SDPAnchorDateIterator,
            SDPAnchorDateIterator.iterator_id,
            SDPAnchorDateIterator.iterator_date_name,
            SDPAnchorDateIterator.is_deleted,
            SDPAnchorDateIterator.extra,
        ),
        (
            SDPTaskCompletionReason,
            SDPTaskCompletionReason.completion_id,
            SDPTaskCompletionReason.completion_desc,
            SDPTaskCompletionReason.is_deleted,
            SDPTaskCompletionReason.extra,
        ),
        (
            V2SalesLevel,
            V2SalesLevel.sl_id,
            func.to_json(
                func.object_construct(
                    "node_level1",
                    V2SalesLevel.node_level1,
                    "node_level2",
                    V2SalesLevel.node_level2,
                    "node_level3",
                    V2SalesLevel.node_level3,
                    "node_level4",
                    V2SalesLevel.node_level4,
                    "node_segment",
                    V2SalesLevel.node_segment,
                )
            ).label("name"),
            literal("F").label("is_deleted"),
            func.parse_json('{"format": "json"}').label("extra"),
        ),
        (
            V2BookingOverrideReason,
            V2BookingOverrideReason.booking_override_reason_id,
            V2BookingOverrideReason.booking_override_reason,
            V2BookingOverrideReason.is_deleted,
            literal_column("null").label("extra"),
        ),
    )

    def fetch_model(
        model: tuple["Type[V2MetadataBase]", "Any", "Any", "Any", "Optional[Any]"],
    ):
        table, id_column, name_column, is_deleted_column, extra = model
        table_name_inner = table.__tablename__

        # noinspection PyArgumentList
        return select(
            literal(table_name_inner).label("table"),
            id_column.label("id"),
            name_column.label("name"),
            is_deleted_column.label("is_deleted"),
            extra,
        ).select_from(table)

    # Union all the select statements
    union_raw = union_all(*[fetch_model(model) for model in dc_models])

    # Type coerce the .extra column
    # noinspection PyArgumentList
    union_select = select(
        union_raw.c.table,
        union_raw.c.id,
        union_raw.c.name,
        union_raw.c.is_deleted,
        type_coerce(union_raw.c.extra, JSONVarchar).label("extra"),
    )

    # Execute the union
    rows = session.execute(union_select).all()
    results = defaultdict(list)
    for row in rows:
        results[row.table].append(
            {
                "id": row.id,
                "value": row.name,
                "is_deleted": row.is_deleted,
                "extra": row.extra,
            }
        )

    return [
        V2TableTypeMapping(table_name=table_name, mappings=table_mappings)
        for table_name, table_mappings in results.items()
    ]
