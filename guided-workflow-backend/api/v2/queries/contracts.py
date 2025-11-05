from sqlalchemy import Integer, String, and_, bindparam, case, func, text
from sqlmodel import select

from api.v2.orm import (
    V2AssetMgtType,
    V2CamEngagement,
    V2Contract,
    V2ContractType,
    V2Engagement,
    V2MonitorType,
    V2User,
)
from api.v2.orm.bookings.bookings import V2BookingContracts
from api.v2.orm.bookings.extensions import V2BookingContractsExtensions
from api.v2.orm.bookings.users import (
    V2BookingResponsibleUsers,
    V2BookingToEngagementResponsibleUser,
)
from api.v2.orm.contracts import (
    V2BuyingPrograms,
    V2ManagedContracts,
    V2PricingModel,
    V2ServicePlans,
)


def query_engagement_contracts(dc_engagement_id: int, cisco_cco_id: str):
    contracts_query = (
        select(V2Contract)
        .join(V2Engagement)
        .join(V2CamEngagement)
        .join(V2User)
        .join(V2ContractType)
        .join(V2AssetMgtType)
        .join(V2MonitorType)
        .where(V2User.cisco_cco_id == cisco_cco_id)
        .where(V2Engagement.dc_engagement_id == dc_engagement_id)
        .where(V2Contract.is_deleted == "F")
    )
    return contracts_query


def query_engagement_booking_contracts(
    dc_engagement_id: int, cisco_cco_id: str, booking_contract: int | None
):
    """
    Query for booking contracts with extensions and responsible users using ORM.

    Args:
        dc_engagement_id: The engagement ID to filter by
        cisco_cco_id: The user's cisco_cco_id for determining edit permissions
        booking_contract: Optional booking contract ID to filter by specific contract

    Returns:
        SQLAlchemy select statement that returns JSON objects containing booking
        contract details with responsible users and managed service contracts
    """

    # Extensions CTE - get the latest extension end date for each booking contract
    extensions_cte = (
        select(
            V2BookingContractsExtensions.booking_contract,
            func.count(V2BookingContractsExtensions.booking_contract).label(
                "extended_count"
            ),
            func.max(V2BookingContractsExtensions.extension_end_date).label(
                "effective_end_date"
            ),
        )
        .where(V2BookingContractsExtensions.is_deleted == "F")
        .group_by(V2BookingContractsExtensions.booking_contract)
        .cte("extensions_cte")
    )

    # Main booking query with all the joins
    booking_query = (
        select(
            V2BookingContracts.booking_contract,
            V2BookingContracts.account_name,
            V2BookingContracts.agreement_start_date,
            V2BookingContracts.agreement_end_date,
            func.coalesce(
                extensions_cte.c.effective_end_date,
                V2BookingContracts.agreement_end_date,
            ).label("effective_end_date"),
            func.coalesce(V2ServicePlans.sold_as_service_name, "UNSET").label(
                "sold_as_service_name"
            ),
            func.coalesce(V2PricingModel.pricing_model_name, "UNSET").label(
                "sold_as_pricing_model"
            ),
            func.coalesce(V2BuyingPrograms.buying_program_name, "UNSET").label(
                "sold_as_buying_program"
            ),
            V2BookingToEngagementResponsibleUser.dc_engagement_id,
            V2BookingToEngagementResponsibleUser.dc_user_id,
            V2User.cisco_cco_id,
            case((V2User.cisco_cco_id == cisco_cco_id, "T"), else_="F").label(
                "is_editable"
            ),
        )
        .join(
            V2BookingResponsibleUsers,
            and_(
                V2BookingResponsibleUsers.booking_contract
                == V2BookingContracts.booking_contract,
                V2BookingResponsibleUsers.is_deleted == "F",
            ),
        )
        .join(
            V2User,
            and_(
                V2User.user_id == V2BookingResponsibleUsers.dc_user_id,
                V2User.is_deleted == "F",
            ),
        )
        .join(
            V2BookingToEngagementResponsibleUser,
            and_(
                V2BookingToEngagementResponsibleUser.booking_contract
                == V2BookingResponsibleUsers.booking_contract,
                V2BookingToEngagementResponsibleUser.dc_user_id
                == V2BookingResponsibleUsers.dc_user_id,
                V2BookingToEngagementResponsibleUser.is_deleted == "F",
            ),
        )
        .join(
            V2PricingModel,
            V2PricingModel.pricing_type_id
            == V2BookingContracts.sold_as_pricing_type_id,
        )
        .join(
            V2BuyingPrograms,
            V2BuyingPrograms.buying_program_type_id
            == V2BookingContracts.buying_program_type_id,
        )
        .join(
            V2ServicePlans,
            V2BookingContracts.sold_as_service_type_id
            == V2ServicePlans.service_type_id,
        )
        .outerjoin(
            extensions_cte,
            V2BookingContracts.booking_contract == extensions_cte.c.booking_contract,
        )
        .where(
            and_(
                V2BookingToEngagementResponsibleUser.dc_engagement_id
                == dc_engagement_id,
                V2BookingContracts.is_deleted == "F",
                V2BookingToEngagementResponsibleUser.is_deleted == "F",
                V2BookingResponsibleUsers.is_deleted == "F",
                V2User.is_deleted == "F",
            )
        )
    )

    # Apply booking contract filter if provided
    if booking_contract is not None:
        booking_query = booking_query.where(
            V2BookingContracts.booking_contract == booking_contract
        )

    booking_query = booking_query.cte("booking")

    # Contracts CTE - aggregate managed service contracts
    contracts_cte = (
        select(
            booking_query.c.booking_contract,
            booking_query.c.dc_user_id,
            booking_query.c.dc_engagement_id,
            func.array_agg(
                func.distinct(
                    func.object_construct_keep_null(
                        "contract_number",
                        V2ManagedContracts.contract_number,
                        "allowed_service_levels",
                        V2ManagedContracts.allowed_service_levels,
                        "contract_name",
                        V2ManagedContracts.contract_name,
                        "notes",
                        V2ManagedContracts.notes,
                    )
                )
            ).label("managed_json_object"),
        )
        .select_from(booking_query)
        .outerjoin(
            V2ManagedContracts,
            and_(
                V2ManagedContracts.dc_user_id == booking_query.c.dc_user_id,
                V2ManagedContracts.booking_contract == booking_query.c.booking_contract,
                V2ManagedContracts.dc_engagement_id == booking_query.c.dc_engagement_id,
                V2ManagedContracts.is_deleted == "F",
            ),
        )
        .group_by(
            booking_query.c.dc_user_id,
            booking_query.c.dc_engagement_id,
            booking_query.c.booking_contract,
        )
    ).cte("contracts")

    # Final query - combine everything and create JSON response
    final_query = (
        select(
            func.to_json(
                func.object_construct_keep_null(
                    "booking_contract",
                    booking_query.c.booking_contract,
                    "account_name",
                    booking_query.c.account_name,
                    "agreement_start_date",
                    booking_query.c.agreement_start_date,
                    "agreement_end_date",
                    booking_query.c.agreement_end_date,
                    "effective_end_date",
                    booking_query.c.effective_end_date,
                    "sold_as_service_name",
                    booking_query.c.sold_as_service_name,
                    "sold_as_pricing_model",
                    booking_query.c.sold_as_pricing_model,
                    "sold_as_buying_program",
                    booking_query.c.sold_as_buying_program,
                    "dc_engagement_id",
                    booking_query.c.dc_engagement_id,
                    "responsible_users",
                    func.array_agg(
                        func.distinct(
                            func.object_construct_keep_null(
                                "responsible_user",
                                booking_query.c.dc_user_id,
                                "responsible_user_cco",
                                booking_query.c.cisco_cco_id,
                                "is_block_owner",
                                booking_query.c.is_editable,
                                "managed_contracts",
                                func.object_construct_keep_null(
                                    "contracts", contracts_cte.c.managed_json_object
                                ),
                            )
                        )
                    ),
                )
            ).label("json"),
            booking_query.c.dc_engagement_id,
            booking_query.c.booking_contract,
            booking_query.c.account_name,
        )
        .select_from(
            booking_query.join(
                contracts_cte,
                and_(
                    booking_query.c.booking_contract
                    == contracts_cte.c.booking_contract,
                    booking_query.c.dc_engagement_id
                    == contracts_cte.c.dc_engagement_id,
                    contracts_cte.c.dc_user_id == booking_query.c.dc_user_id,
                ),
            )
        )
        .group_by(
            booking_query.c.booking_contract,
            booking_query.c.account_name,
            booking_query.c.agreement_start_date,
            booking_query.c.agreement_end_date,
            booking_query.c.effective_end_date,
            booking_query.c.sold_as_service_name,
            booking_query.c.sold_as_pricing_model,
            booking_query.c.dc_engagement_id,
            booking_query.c.sold_as_buying_program,
        )
    )

    return final_query
