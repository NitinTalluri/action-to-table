import json
import logging
from collections import defaultdict
from datetime import timedelta
from decimal import Decimal
from enum import IntFlag, auto
from json import JSONDecodeError
from typing import (
    TYPE_CHECKING,
    Callable,
    Concatenate,
    NamedTuple,
    Optional,
    ParamSpec,
    Type,
    TypeVar,
)

from fastapi.encoders import jsonable_encoder
from sqlalchemy import (
    Boolean,
    and_,
    func,
    insert,
    text,
    update,
)
from sqlalchemy.orm import load_only
from sqlmodel import select
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR

from api.v2.orm import (
    booking_contracts_table,
)

from ..queries.stored_proc import make_stored_proc_statement, parse_stored_proc_result
from . import ServiceException, SessionMixin


class ServiceTypeFlag(IntFlag):
    HW = auto()
    SW = auto()
    HW_SW = HW | SW


logger = logging.getLogger("api")

if TYPE_CHECKING:
    from sqlmodel import Session

    from api.dependencies.queries import TFetchBookingServiceTypeTableReturn
    from api.v2.models import (
        V2DisengagementModel,
        V2ModifyBookingDcTypes,
        V2ProspectiveBookingEditPayload,
        V2ProspectiveBookingPayload,
        V2VerifiedBookingAssignmentModify,
    )
    from api.v2.models.contracts import V2BookingEngagementAssignment
    from api.v2.orm import (
        V2BookingContractsExtensions,
        V2User,
    )

    from ..models.manager.bookings import (
        V2ModifyBookingDefaultEngagement,
    )

P = ParamSpec("P")
R = TypeVar("R")


def dispatch_booking_change(
    func: Callable[Concatenate["ManagerBookingsService", P], R],
) -> Callable[Concatenate["ManagerBookingsService", int, P], R]:
    def wrapper(
        self: "ManagerBookingsService",
        booking_contract: int,
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> R:
        result = func(self, booking_contract, *args, **kwargs)
        self.rebuild_sdp_for_booking_contract(booking_contract, sub_task_ids=None)
        return result

    return wrapper


class EngagementUserIds(NamedTuple):
    dc_user_id: int
    dc_engagement_id: int


class ManagerBookingsService(SessionMixin):
    _PRIMARY_ROLE = "CAM-PRIMARY"
    _BACKUP_ROLE = "CAM-BACKUP"
    _CXEA_DESIGNATED = "CXEA - Designated"
    pending_dispatches: set[int]
    """
    This orchestrates unit of work operations for manager bookings requiring dml operations.
    
    Attributes
    ----------
    pending_dispatches : set[int]
        When exited from a context manager, any booking contract ids in this set will be dispatched
        to the stored procedure
    
    """

    def __init__(
        self,
        session: "Session",
        booking_types: "TFetchBookingServiceTypeTableReturn",
        ignore_dispatch: bool,
    ):
        super().__init__(session)

        self.booking_types = booking_types
        self.user_roles = {
            row["value"]: row["id"] for row in booking_types["dc_bookings_user_role"]
        }
        self.service_type_map = {
            row["id"]: self._parse_service_type(row["value"])
            for row in booking_types["dc_sold_as_service_types"]
        }
        self.buying_program_map = {
            row["value"]: row["id"] for row in booking_types["dc_buying_programs"]
        }
        self.pending_dispatches = set()
        self.ignore_dispatch = ignore_dispatch

    def __exit__(
        self, exc_type: Optional[Type[Exception]], exc_val: Optional[Exception], exc_tb
    ):
        if not self.pending_dispatches:
            return super().__exit__(exc_type, exc_val, exc_tb)
        if self.ignore_dispatch:
            logger.info(
                "%s : Ignoring SDP rebuild for Booking Contracts: %s",
                self.__class__.__name__,
                self.pending_dispatches,
            )
            self.pending_dispatches.clear()
            return super().__exit__(exc_type, exc_val, exc_tb)

        logger.info(
            "%s : Rebuilding SDP for Booking Contracts: %s",
            self.__class__.__name__,
            self.pending_dispatches,
        )
        for booking_contract in self.pending_dispatches:
            self.rebuild_sdp_for_booking_contract(
                booking_contract=booking_contract, sub_task_ids=None
            )
        self.pending_dispatches.clear()
        return super().__exit__(exc_type, exc_val, exc_tb)

    @property
    def backup_role_id(self):
        value = self.user_roles.get(self._BACKUP_ROLE)
        if value is None:
            raise ServiceException(f"{self._BACKUP_ROLE} not found", 500)
        return value

    @property
    def primary_role_id(self):
        value = self.user_roles.get(self._PRIMARY_ROLE)
        if value is None:
            raise ServiceException(f"{self._PRIMARY_ROLE} not found", 500)
        return value

    @property
    def buying_program_cxea_designated_id(self):
        value = self.buying_program_map.get(self._CXEA_DESIGNATED)
        if value is None:
            raise ServiceException(f"Id for '{self._CXEA_DESIGNATED}' not found", 500)
        return value

    def rebuild_sdp_for_booking_contract(
        self, booking_contract: int, sub_task_ids: list[int] | None
    ):
        """
        Should be called whenever one of:
        - SOLD_AS_SERVICE
        - PRICING MODEL
        - BUYING PROGRAM
        - ASSIGNMENTS
        - EXTENSIONS

        This can be triggered to run after a method call by using the dispatch_booking_change decorator

        If sub_task_ids is provided and buying program is CXEA Scale, it will only rebuild SDP for those sub_tasks.
        """
        params = {"booking_contract": booking_contract, "sub_task_ids": sub_task_ids}

        stmt = make_stored_proc_statement().bindparams(
            proc_name="dc_sdp_contract_changes",
            params=json.dumps(params, separators=(",", ":")),
        )

        try:
            raw_result = self.session.execute(stmt).scalar()
            self.session.commit()

            result = parse_stored_proc_result(raw_result)
            msg = result.get("message")

            if not result.get("success"):
                raise RuntimeError(msg)

            logger.info(
                "Rebuilt SDP for booking contract %s, sub_task_ids: %s, message: %s",
                booking_contract,
                sub_task_ids,
                msg,
            )
        except Exception as e:
            logger.error(
                "Failed to rebuild SDP for booking contract %s, sub_task_ids: %s: %r",
                booking_contract,
                sub_task_ids,
                e,
            )
            self.session.rollback()
            raise ServiceException(
                code=HTTP_500_INTERNAL_SERVER_ERROR, msg=f"{e!r}"
            ) from e

    def delete_prospective_booking(self, booking_contract: int, requestor: "V2User"):
        """Prospective bookings can be deleted by the user who created them"""
        if booking_contract >= 0:
            raise ServiceException("Only prospective bookings can be deleted", 400)
        from api.v2.orm import booking_contracts_table

        stmt = (
            select(booking_contracts_table.c.booking_contract)
            .where(booking_contracts_table.c.booking_contract == booking_contract)
            .where(booking_contracts_table.c.is_deleted == "F")
            .where(
                booking_contracts_table.c.claimed_and_managed_by == requestor.user_id
            )
        )

        db_booking_contract = self.session.exec(stmt).one_or_none()
        if not db_booking_contract:
            raise ServiceException(
                f"Booking Contract {booking_contract} not found or not claimed by user",
                404,
            )

        soft_delete_stmt = (
            update(booking_contracts_table)
            .where(booking_contracts_table.c.booking_contract == booking_contract)
            .where(booking_contracts_table.c.is_deleted == "F")
            .where(
                booking_contracts_table.c.claimed_and_managed_by == requestor.user_id
            )
            .values(
                is_deleted="T",
                updated_by=requestor.cisco_cco_id,
                update_dtm=func.now(),
            )
        )
        self.session.execute(soft_delete_stmt)

    def update_prospective_booking(
        self, payload: "V2ProspectiveBookingEditPayload", requestor: "V2User"
    ):
        if payload.booking_contract >= 0:
            raise ServiceException("Only prospective bookings can be updated", 400)

        from api.v2.orm import (
            V2BuyingPrograms,
            V2PricingModel,
            V2ServicePlans,
            V2Theater,
            booking_contracts_table,
        )

        booking_query = (
            select(booking_contracts_table.c.booking_contract)
            .where(
                booking_contracts_table.c.booking_contract == payload.booking_contract
            )
            .where(booking_contracts_table.c.is_deleted == "F")
            .where(
                booking_contracts_table.c.claimed_and_managed_by == requestor.user_id
            )
            .exists()
        )

        # noinspection PyTypeChecker,PydanticTypeChecker
        if not self.session.exec(select(booking_query)).one():
            raise ServiceException(
                f"Booking Contract {payload.booking_contract} not found or not claimed by user",
                404,
            )

        changed_data = payload.dict(exclude_unset=True, exclude={"booking_contract"})
        from api.v2.queries import QueryMembership

        members_query = QueryMembership()

        if changed_data.get("booked_theater_id"):
            members_query.add_orm_membership(
                V2Theater, [changed_data["booked_theater_id"]]
            )
        if changed_data.get("sold_as_service_type_id"):
            members_query.add_orm_membership(
                V2ServicePlans, [changed_data["sold_as_service_type_id"]]
            )
        if changed_data.get("sold_as_pricing_type_id"):
            members_query.add_orm_membership(
                V2PricingModel, [changed_data["sold_as_pricing_type_id"]]
            )
        if changed_data.get("buying_program_type_id"):
            members_query.add_orm_membership(
                V2BuyingPrograms, [changed_data["buying_program_type_id"]]
            )

        if not members_query.empty:
            non_existent_dc_types = self.session.exec(members_query.build()).all()
            if non_existent_dc_types:
                raise ServiceException(
                    f"DC Types not found: {[(row.type, row.id) for row in non_existent_dc_types]}",
                    404,
                )

        update_stmt = (
            update(booking_contracts_table)
            .where(
                booking_contracts_table.c.booking_contract == payload.booking_contract
            )
            .where(booking_contracts_table.c.is_deleted == "F")
            .where(
                booking_contracts_table.c.claimed_and_managed_by == requestor.user_id
            )
            .values(
                **changed_data, updated_by=requestor.cisco_cco_id, update_dtm=func.now()
            )
        )

        self.session.execute(update_stmt)
        self.pending_dispatches.add(payload.booking_contract)

    def create_prospective_booking(
        self, payload: "V2ProspectiveBookingPayload", requestor: "V2User"
    ) -> int:
        """Creating a prospective booking involves creating a booking contract and conditionally applying allocations"""
        from api.v2.orm import (
            ProspectiveBookingSequence,
            V2BookingContractType,
            V2BuyingPrograms,
            V2PricingModel,
            V2ServicePlans,
            V2Theater,
            booking_contracts_table,
        )
        from api.v2.queries import QueryMembership

        query_members = (
            QueryMembership()
            .add_orm_membership(V2Theater, [payload.booked_theater_id])
            .add_orm_membership(V2ServicePlans, [payload.sold_as_service_type_id])
            .add_orm_membership(V2PricingModel, [payload.sold_as_pricing_type_id])
            .add_orm_membership(V2BuyingPrograms, [payload.buying_program_type_id])
            .build()
        )

        non_existent_dc_types = self.session.exec(query_members).all()
        if non_existent_dc_types:
            raise ServiceException(
                f"DC Types not found: {[(row.type, row.id) for row in non_existent_dc_types]}",
                404,
            )

        # The booking_contract_type_id must be a prospective booking
        booking_type_query = (
            select(
                V2BookingContractType.is_budgeted.label("is_budgeted"),
            )
            .where(V2BookingContractType.is_prospective)
            .where(V2BookingContractType.is_deleted == "F")
            .where(V2BookingContractType.id == payload.booking_contract_type_id)
        )

        is_budgeted = self.session.exec(booking_type_query).one_or_none()
        if is_budgeted is None:
            raise ServiceException(
                f"Booking Contract Type {payload.booking_contract_type_id} is not a prospective booking or was not found",
                404,
            )

        zeroed = lambda x: 0 if not is_budgeted else x

        # Manually get a booking contract id from a different sequence
        booking_contract = self.session.exec(
            select(ProspectiveBookingSequence.next_value())
        ).one()

        stmt = insert(booking_contracts_table).values(
            booking_contract=booking_contract,
            created_by=requestor.cisco_cco_id,
            create_dtm=func.now(),
            is_deleted="F",
            account_name=payload.account_name,
            booked_sav_1=None,
            booked_sav_2=None,
            booked_sav_3=None,
            booked_theater_id=payload.booked_theater_id,
            sold_as_service_type_id=payload.sold_as_service_type_id,
            sold_as_pricing_type_id=payload.sold_as_pricing_type_id,
            buying_program_type_id=payload.buying_program_type_id,
            booking_contract_type_id=payload.booking_contract_type_id,
            booked_usd=zeroed(payload.booked_usd),
            agreement_start_date=payload.agreement_start_date,
            agreement_end_date=payload.agreement_end_date,
            booking_country=payload.booking_country,
            cam_revenue_usd=zeroed(payload.cam_revenue_usd),
            cam_cost_usd=zeroed(payload.cam_cost_usd),
            souced_allocation=zeroed(payload.sourced_allocation),
            sold_as_sw_allocation=zeroed(payload.sold_as_sw_allocation),
            sold_as_hw_allocation=zeroed(payload.sold_as_hw_allocation),
            claimed_and_managed_by=requestor.user_id,
            allocation_fte_sw_ratio=0.5,
            allocation_fte_hw_ratio=0.5,
        )

        self.session.execute(stmt)
        self.pending_dispatches.add(booking_contract)
        return booking_contract

    def update_booking_defaults(
        self,
        booking_contract: int,
        requestor: "V2User",
        payload: "V2ModifyBookingDefaultEngagement",
    ):
        """Update claimed booking contract defaults. Currently only allows updating the default engagement id."""
        from api.v2.orm import V2BookingContracts, V2Engagement

        # Ensure booking contract exists
        query_exists = (
            select(V2BookingContracts)
            .where(V2BookingContracts.booking_contract == booking_contract)
            .where(V2BookingContracts.is_deleted == "F")
            .options(
                load_only(
                    V2BookingContracts.booking_contract,
                    V2BookingContracts.dc_engagement_id_default,
                )
            )
        )

        db_booking = self.session.exec(query_exists).one_or_none()

        if not db_booking:
            raise ServiceException(
                f"Booking Contract {booking_contract} not found", 404
            )

        # Verify dc_engagement_id_default exists in dc_engagement_hdr
        engagement_exists = self.session.exec(
            select(V2Engagement.dc_engagement_id)
            .where(V2Engagement.is_deleted == "F")
            .where(V2Engagement.dc_engagement_id == payload.dc_engagement_id_default)
        ).one_or_none()
        if not engagement_exists:
            raise ServiceException(
                f"Engagement ID {payload.dc_engagement_id_default} not found", 404
            )

        update_stmt = (
            update(booking_contracts_table)
            .where(booking_contracts_table.c.booking_contract == booking_contract)
            .where(booking_contracts_table.c.is_deleted == "F")
            .values(
                dc_engagement_id_default=payload.dc_engagement_id_default,
                updated_by=requestor.cisco_cco_id,
                update_dtm=func.now(),
            )
        )

        self.session.execute(update_stmt)

    def update_booking_dc_types(
        self,
        booking_contract: int,
        requestor: "V2User",
        payload: "V2ModifyBookingDcTypes",
    ):
        from api.v2.orm import (
            V2BookingContracts,
            V2BuyingPrograms,
            V2PricingModel,
            V2ServicePlans,
            V2Theater,
        )
        from api.v2.queries import QueryMembership

        query_members = (
            QueryMembership()
            .add_orm_membership(V2Theater, [payload.booked_theater_id])
            .add_orm_membership(V2ServicePlans, [payload.sold_as_service_type_id])
            .add_orm_membership(V2PricingModel, [payload.sold_as_pricing_type_id])
            .add_orm_membership(V2BuyingPrograms, [payload.buying_program_type_id])
            .build()
        )

        non_existent_dc_types = self.session.exec(query_members).all()
        if non_existent_dc_types:
            raise ServiceException(
                f"DC Types not found: {[(row.type, row.id) for row in non_existent_dc_types]}",
                404,
            )

        db_booking_query = self._db_booking_query(booking_contract).options(
            load_only(
                V2BookingContracts.booking_contract,
                V2BookingContracts.booked_hw,
                V2BookingContracts.booked_sw,
                V2BookingContracts.sourced_allocation,
                V2BookingContracts.allocation_fte_sw_ratio,
                V2BookingContracts.allocation_fte_hw_ratio,
            )
        )

        db_booking = self.session.exec(db_booking_query).one_or_none()

        if not db_booking:
            raise ServiceException(
                f"Booking Contract {booking_contract} not found", 404
            )

        current_service_type = self._get_booking_service_type(booking_contract)
        proposed_service_type = self.service_type_map[payload.sold_as_service_type_id]

        shifted_service_from = (
            None
            if current_service_type in proposed_service_type
            else current_service_type & ~proposed_service_type
        )

        base_values = {
            "sold_as_service_type_id": payload.sold_as_service_type_id,
            "sold_as_pricing_type_id": payload.sold_as_pricing_type_id,
            "buying_program_type_id": payload.buying_program_type_id,
            "booked_theater_id": payload.booked_theater_id,
            "updated_by": requestor.cisco_cco_id,
            "update_dtm": func.now(),
        }

        match shifted_service_from, proposed_service_type:
            case ServiceTypeFlag.HW, ServiceTypeFlag.SW:
                # HW -> 0, Sw -> Sw + HW
                # Switching from HW only to SW only

                base_values.update(
                    {
                        "sold_as_hw_allocation": 0,
                        "sold_as_sw_allocation": Decimal(str(db_booking.booked_sw))
                        + Decimal(str(db_booking.booked_hw)),
                        "allocation_fte_hw_ratio": 0,
                        "allocation_fte_sw_ratio": 1,
                    }
                )
                stmt = text(
                    """
                    UPDATE DC_BOOKINGS_CONTRACTS_RESPONSIBLE_USERS
                    SET SUB_ALLOCATION_HW = 0,
                    UPDATED_BY = :requestor,
                    UPDATE_DTM = CURRENT_TIMESTAMP
                    WHERE BOOKING_CONTRACT = :booking_contract
                    AND IS_DELETED = 'F'
                """
                ).bindparams(
                    booking_contract=booking_contract,
                    requestor=requestor.cisco_cco_id,
                )
                self.session.execute(stmt)
            case ServiceTypeFlag.SW, ServiceTypeFlag.HW:
                # Sw -> 0, HW -> HW + SW
                # Switching from SW only to HW only
                base_values.update(
                    {
                        "sold_as_sw_allocation": 0,
                        "sold_as_hw_allocation": Decimal(str(db_booking.booked_sw))
                        + Decimal(str(db_booking.booked_hw)),
                        "allocation_fte_hw_ratio": 1,
                        "allocation_fte_sw_ratio": 0,
                    }
                )
                stmt = text(
                    """
                    UPDATE DC_BOOKINGS_CONTRACTS_RESPONSIBLE_USERS
                    SET SUB_ALLOCATION_SW = 0,
                    UPDATED_BY = :requestor,
                    UPDATE_DTM = CURRENT_TIMESTAMP
                    WHERE BOOKING_CONTRACT = :booking_contract
                    AND IS_DELETED = 'F'
                """
                ).bindparams(
                    booking_contract=booking_contract,
                    requestor=requestor.cisco_cco_id,
                )
                self.session.execute(stmt)
            case None, ServiceTypeFlag.HW_SW:
                # Switching from HW or SW to HW_SW
                match (
                    db_booking.allocation_fte_hw_ratio,
                    db_booking.allocation_fte_sw_ratio,
                ):
                    case None, None:  # Assume even split
                        db_ratio_hw = Decimal("0.5")
                        db_ratio_sw = Decimal("0.5")
                    case Decimal(), Decimal():
                        db_ratio_hw = db_booking.allocation_fte_hw_ratio
                        db_ratio_sw = db_booking.allocation_fte_sw_ratio
                    case Decimal(), None:
                        db_ratio_hw = db_booking.allocation_fte_hw_ratio
                        db_ratio_sw = Decimal("1.0") - db_ratio_hw
                    case None, Decimal():
                        db_ratio_sw = db_booking.allocation_fte_sw_ratio
                        db_ratio_hw = Decimal("1.0") - db_ratio_sw
                    case _:
                        raise ServiceException(
                            msg="Logic Error, Unhandled Case", code=500
                        )

                if not (db_ratio_hw + db_ratio_sw == Decimal("1.0")):
                    raise ServiceException(
                        f"Allocations {db_ratio_hw} + {db_ratio_sw} do not sum to 1",
                        500,
                    )

                base_values.update(
                    {
                        "allocation_fte_hw_ratio": db_ratio_hw,
                        "allocation_fte_sw_ratio": db_ratio_sw,
                    }
                )

                if current_service_type == ServiceTypeFlag.HW:
                    # Copy HW to SW for users
                    stmt = text(
                        """
                        UPDATE DC_BOOKINGS_CONTRACTS_RESPONSIBLE_USERS
                        SET SUB_ALLOCATION_SW = SUB_ALLOCATION_HW,
                        UPDATED_BY = :requestor,
                        UPDATE_DTM = CURRENT_TIMESTAMP
                        WHERE BOOKING_CONTRACT = :booking_contract
                        AND IS_DELETED = 'F'
                        """
                    ).bindparams(
                        booking_contract=booking_contract,
                        requestor=requestor.cisco_cco_id,
                    )
                    self.session.execute(stmt)
                elif current_service_type == ServiceTypeFlag.SW:
                    # Copy SW to HW for users
                    stmt = text(
                        """
                        UPDATE DC_BOOKINGS_CONTRACTS_RESPONSIBLE_USERS
                        SET SUB_ALLOCATION_HW = SUB_ALLOCATION_SW,
                        UPDATED_BY = :requestor,
                        UPDATE_DTM = CURRENT_TIMESTAMP
                        WHERE BOOKING_CONTRACT = :booking_contract
                        AND IS_DELETED = 'F'
                        """
                    ).bindparams(
                        booking_contract=booking_contract,
                        requestor=requestor.cisco_cco_id,
                    )
                    self.session.execute(stmt)

                total_alloc = Decimal(str(db_booking.sourced_allocation))
                hw_alloc = total_alloc * db_ratio_hw
                sw_alloc = total_alloc - hw_alloc
                if not (hw_alloc + sw_alloc == total_alloc):
                    raise ServiceException(
                        f"Allocations {hw_alloc} + {sw_alloc} do not sum to total allocation {total_alloc}",
                        500,
                    )

                base_values.update(
                    {
                        "sold_as_hw_allocation": hw_alloc,
                        "sold_as_sw_allocation": sw_alloc,
                    }
                )

        update_stmt = (
            update(V2BookingContracts)
            .where(V2BookingContracts.booking_contract == booking_contract)
            .where(V2BookingContracts.is_deleted == "F")
            .where(V2BookingContracts.claimed_and_managed_by == requestor.user_id)
            .values(base_values)
        )
        self.session.execute(update_stmt)
        self.pending_dispatches.add(booking_contract)

    def claim_booking(
        self,
        requestor: "V2User",
        booking_contract: int,
        renewal_sources: Optional[list[int]],
        dc_engagement_id_default: Optional[int],
        booking_override_reason_id: Optional[int],
    ):
        """Claim a booking"""

        # Ensure booking contract exists

        from api.v2.orm import V2BookingContracts

        query_exists = (
            select(V2BookingContracts)
            .where(V2BookingContracts.booking_contract == booking_contract)
            .where(V2BookingContracts.is_deleted == "F")
            .options(
                load_only(
                    V2BookingContracts.booking_contract,
                    V2BookingContracts.claimed_and_managed_by,
                )
            )
        )

        booking = self.session.exec(query_exists).one()
        is_cxea_scale = self._is_cxea_scale_booking(booking_contract)

        # Business ask - CXEA Scale can be claimed even if existing claimed
        if booking.claimed_and_managed_by and not is_cxea_scale:
            raise ServiceException(
                f"Booking Contract {booking_contract} already claimed by user id {booking.claimed_and_managed_by}",
                409,
            )

        # Check if CXEA Scale booking requires override reason
        if is_cxea_scale and booking_override_reason_id is None:
            raise ServiceException(
                "CXEA Scale bookings require an override reason to be claimed",
                400,
            )

        if renewal_sources:
            query_renewal_sources = self._query_booking_contract_memberships(
                renewal_sources
            )
            missing_sources = self.session.exec(query_renewal_sources).all()
            if missing_sources:
                raise ServiceException(
                    f"Cannot set renewal for booking contract: {booking_contract},"
                    f" {[row.id for row in missing_sources]} not found.",
                    404,
                )

        claim_values = {
            "claimed_and_managed_by": requestor.user_id,
            "dc_engagement_id_default": dc_engagement_id_default,
            "updated_by": requestor.cisco_cco_id,
            "update_dtm": func.now(),
        }
        # If this was a CXEA Scale Booking, then during the claim action we update to CXEA Designated
        # This is special exception from business. We

        if is_cxea_scale:
            # Also update the buying program to CXEA Designated (#2)
            claim_values.update(
                {
                    "buying_program_type_id": self.buying_program_cxea_designated_id,
                }
            )
            # Track the override in DC_BOOKING_OVERRIDE
            self._store_booking_override(
                booking_contract=booking_contract,
                booking_override_reason_id=booking_override_reason_id,
                requestor=requestor,
            )

            update_stmt = (
                update(V2BookingContracts)
                .where(V2BookingContracts.booking_contract == booking_contract)
                .where(V2BookingContracts.is_deleted == "F")
                # Intentional to not check claimed_and_managed_by
                .values(**claim_values)
            )

        else:
            update_stmt = (
                update(V2BookingContracts)
                .where(V2BookingContracts.booking_contract == booking_contract)
                .where(V2BookingContracts.is_deleted == "F")
                .where(V2BookingContracts.claimed_and_managed_by == None)
                .values(**claim_values)
            )

        self.session.execute(update_stmt)

        # Renewal sources
        if renewal_sources:
            from api.v2.orm import V2BookingContractsLineage

            insert_stmt = insert(V2BookingContractsLineage).values(
                [
                    {
                        "parent_booking_contract": source,
                        "child_booking_contract": booking_contract,
                        "create_dtm": func.now(),
                        "created_by": requestor.cisco_cco_id,
                        "is_deleted": "F",
                    }
                    for source in renewal_sources
                ]
            )
            self.session.execute(insert_stmt)

    def unclaim_booking(self, requestor: "V2User", booking_contract: int):
        """Unclaim a booking"""

        # Ensure booking contract exists

        from api.v2.orm import V2BookingContracts, V2BookingContractsLineage

        query_exists = (
            select(V2BookingContracts)
            .where(V2BookingContracts.booking_contract == booking_contract)
            .where(V2BookingContracts.is_deleted == "F")
            .options(
                load_only(
                    V2BookingContracts.booking_contract,
                    V2BookingContracts.claimed_and_managed_by,
                )
            )
        )

        booking = self.session.exec(query_exists).one()

        if booking.claimed_and_managed_by != requestor.user_id:
            raise ServiceException("Booking Contract is claimed by another user", 403)

        # Claim booking
        update_stmt = (
            update(V2BookingContracts)
            .where(V2BookingContracts.booking_contract == booking_contract)
            .where(V2BookingContracts.is_deleted == "F")
            .where(V2BookingContracts.claimed_and_managed_by == requestor.user_id)
            .values(
                claimed_and_managed_by=None,
                updated_by=requestor.cisco_cco_id,
                update_dtm=func.now(),
            )
        )

        renewal_stmt = (
            update(V2BookingContractsLineage)
            .where(
                and_(
                    V2BookingContractsLineage.child_booking_contract
                    == booking_contract,
                    V2BookingContractsLineage.is_deleted == "F",
                )
            )
            .values(
                is_deleted="T",
                updated_by=requestor.cisco_cco_id,
                update_dtm=func.now(),
            )
        )

        self.session.execute(update_stmt)
        self.session.execute(renewal_stmt)

    def disengage_booking_contract(
        self, payload: "V2DisengagementModel", requestor: "V2User"
    ):
        from api.v2.orm import (
            V2BookingContracts,
            V2BookingToEngagementResponsibleUser,
            V2Disengagement,
        )

        query = select(
            V2BookingContracts.booking_contract,
            V2BookingContracts.claimed_and_managed_by,
        ).where(V2BookingContracts.booking_contract == payload.booking_contract)

        result = self.session.exec(query).one_or_none()

        if not result:
            raise ServiceException(
                f"Booking Contract {payload.booking_contract} not found", 404
            )

        if result.claimed_and_managed_by != requestor.user_id:
            raise ServiceException(
                f"Booking Contract {payload.booking_contract} is not claimed by user {requestor.cisco_cco_id}",
                403,
            )

        # V2Disengagement tracks dc_engagement_id which isn't present in payload
        # We query the booking engagement user to hopefully get a single engagement id.
        # Even if multiple, this doesn't really matter so much

        query_engagement = (
            select(
                V2BookingToEngagementResponsibleUser.dc_engagement_id,
            )
            .where(
                V2BookingToEngagementResponsibleUser.booking_contract
                == payload.booking_contract
            )
            .order_by(
                V2BookingToEngagementResponsibleUser.is_deleted,
                V2BookingToEngagementResponsibleUser.create_dtm,
            )
        )

        db_engagement = self.session.exec(query_engagement.limit(1)).one_or_none()
        if not db_engagement:
            db_engagement = 0

        query_disengage = (
            select(V2Disengagement)
            .where(V2Disengagement.booking_contract == payload.booking_contract)
            .where(V2Disengagement.dc_engagement_id == db_engagement)
            .where(V2Disengagement.dc_user_id == requestor.user_id)
            .where(V2Disengagement.is_deleted == "F")
            .exists()
        )

        # noinspection PyTypeChecker,PydanticTypeChecker
        if self.session.exec(select(query_disengage)).one():
            raise ServiceException(
                f"Booking Contract {payload.booking_contract} is already disengaged",
                409,
            )

        db_disengagement = V2Disengagement.create_from_model(
            model=payload,
            dc_engagement_id=db_engagement,
            logged_user=requestor.cisco_cco_id,
            user_id=requestor.user_id,
            session=self.session,
        )
        return db_disengagement

    def set_booking_allocations(
        self,
        booking_contract: int,
        payload: "V2VerifiedBookingAssignmentModify",
        requestor: "V2User",
    ) -> set[EngagementUserIds]:
        """
        Do a PUT like operation to set the allocations for a booking contract.
        This will overwrite any existing allocations.

        Depending on the booking contract's service type, we may ignore sw or hw

        The allocations must sum to 1 for HW_SW, 1 for HW, or 1 for SW.
        The operation must result in having exactly one Primary CAM role per Engagement.

        Returns
        -------
        set[EngagementUserIds]
            A set of tuples containing (dc_user_id, dc_engagement_id) that are newly associated users with the engagement.
            These should be handled by dispatching the appropriate share emit via prefect service

        """

        # Verify that the payload contains a single self.primary_role_id (CAM-PRIMARY) role per engagement
        booking_service_type = self._get_booking_service_type(
            booking_contract=booking_contract
        )
        self._validate_assignments(
            assignments=payload.assignments,
            primary_role_id=self.primary_role_id,
            service_type_flag=booking_service_type,
        )

        # Given the desired allocations, we need to:
        # 1. For each user, ensure they are associated with the booking contract via V2BookingResponsibleUsers
        # 2. For each user, ensure they are associated with the engagement via V2BookingToEngagementResponsibleUser
        # 3. For each user, ensure they are associated with the engagement via V2CamEngagement
        # 4. For each user, if their association is new via V2CamEngagement, share the engagement with them via Prefect
        # 5. Remove any existing associations for the booking contract and engagement

        payload_params = {
            **payload.dict(),
            "requestor_cisco_cco_id": requestor.cisco_cco_id,
        }

        stmt = text(
            """
            CALL IDENTIFIER(:proc_name)(:payload)
            """
        ).bindparams(
            proc_name="put_booking_assignments",
            payload=json.dumps(jsonable_encoder(payload_params), separators=(",", ":")),
        )
        try:
            result = self.session.execute(stmt).scalar()
            logger.info(
                "Result of stored procedure '%s': %s", "put_booking_assignments", result
            )
        except Exception as e:
            self.session.rollback()
            logger.exception(
                "Failed to run stored procedure to set booking allocations with parameters %s",
                payload_params,
            )
            raise ServiceException(f"Error running stored procedure {e!r}", 500) from e
        try:
            result = json.loads(result)
        except JSONDecodeError as e:
            logger.exception(
                "Error parsing JSON result from stored procedure %s with parameters %s",
                "put_booking_assignments",
                payload_params,
            )
            raise ServiceException(
                "Error parsing result from stored procedure", 500
            ) from e

        success = result["success"]
        message = result["message"]
        if not success:
            logger.error(
                "Stored procedure for setting booking allocations completed but did not succeed: %s, %s",
                payload_params,
                message,
            )
            raise ServiceException(message, 500)

        raw_shares = result.get("shares", [])
        shared_with_ids = {
            EngagementUserIds(
                dc_user_id=share.get("dc_user_id"),
                dc_engagement_id=share.get("dc_engagement_id"),
            )
            for share in raw_shares
            if share.get("dc_user_id") and share.get("dc_engagement_id")
        }

        self.pending_dispatches.add(booking_contract)
        logger.info("Shared with IDs: %s", shared_with_ids)
        return shared_with_ids

    def replace_assignment_responsible_user(
        self,
        booking_contract: int,
        prev_user_id: int,
        new_user_id: int,
        requestor: "V2User",
    ) -> bool:
        """

        Run a process where a new user will inherit the allocations assigned to the old user along with the associated role.
        The old user remains associated but with zerod allocations and uses a special "backup" role.
        We ensure the new user is associated with the engagement. If not, we add them and should notify prefect to share canvases.

        This involves several steps:
        1. Verifying database integrity for prev user
            - Ensure the booking contract exists and is not deleted
            - Ensure the booking contract is associated with an engagement
            - Ensure the booking contract is claimed by the logged user
            - Ensure the engagement exists and is not deleted
            - The prev user exists
            - Ensure the prev user is associated with the booking contract (V2BookingToEngagementResponsibleUser)
            - Ensure the prev user has allocations for the booking contract (V2BookingResponsibleUsers)
        2. Verifying database integrity for next user
            - Ensure the next user exists
            - Ensure the next user is either associated with the engagement or add them (V2CamEngagement)
            - Ensure the next user is either associated with the booking contract or add them (V2BookingToEngagementResponsibleUser)
            - Ensure the next user has allocations for the booking contract or add them (V2BookingResponsibleUsers)
        3. Update the allocations for the prev user to zero and assign the backup role
        4. Update the allocations for the next user to the prev user's allocations and role
        5. Update managed service contracts to replace the dc_user_id with the new user where dc_engagement_id matches
           the engagement associated with the booking contract
        """
        proc_name = "replace_responsible_user"
        proc_input = {
            "booking_contract": booking_contract,
            "new_user_id": new_user_id,
            "prev_user_id": prev_user_id,
            "requestor_user_id": requestor.user_id,
            "requestor_cisco_cco_id": requestor.cisco_cco_id,
        }

        stmt = text(
            """
            CALL IDENTIFIER(:proc_name)(:params)
            """
        ).bindparams(
            proc_name=proc_name,
            params=json.dumps(proc_input, separators=(",", ":")),
        )

        try:
            result = self.session.execute(stmt).scalar()
        except Exception as e:
            logger.exception(
                "Error running stored procedure proc_name='%s' with proc_input=%s",
                proc_name,
                proc_input,
            )
            raise ServiceException(
                f"Error running stored procedure {proc_name=}", 500
            ) from e

        try:
            result = json.loads(result)
        except Exception as e:
            logger.exception(
                "Error parsing JSON result from stored procedure proc_name='%s' with proc_input=%s\nresult=%s",
                proc_name,
                proc_input,
                result,
            )
            raise ServiceException(
                f"Error parsing result from stored procedure {proc_name=}", 500
            ) from e

        success, message, code, logs = (
            result.get("success"),
            result.get("message"),
            result.get("code"),
            result.get("logs"),
        )

        if not success:
            logger.error(
                "Error running stored procedure proc_name=%s with proc_input='%s' message='%s' code=%s logs=%s",
                proc_name,
                proc_input,
                message,
                code,
                logs,
            )
            raise ServiceException(message, code)
        needs_shared = result.get("needs_shared")
        logger.info(
            "Successfully ran stored procedure '%s' with '%s', logs=%s",
            proc_name,
            proc_input,
            logs,
        )
        self.pending_dispatches.add(booking_contract)

        return needs_shared

    @dispatch_booking_change
    def extend_booking_contract(
        self,
        booking_contract: int,
        requestor: "V2User",
        duration_days: int,
        extension_count_limit: int,
    ) -> "V2BookingContractsExtensions":
        from api.v2.orm import V2BookingContracts, V2BookingContractsExtensions

        db_booking_query = self._db_booking_query(booking_contract).options(
            load_only(
                V2BookingContracts.booking_contract,
                V2BookingContracts.claimed_and_managed_by,
                V2BookingContracts.agreement_end_date,
            )
        )

        db_booking = self.session.exec(db_booking_query).one_or_none()
        if not db_booking:
            raise ServiceException(
                f"Booking Contract {booking_contract} not found", 404
            )
        if db_booking.claimed_and_managed_by != requestor.user_id:
            raise ServiceException(
                f"Booking Contract {booking_contract} is not claimed by user {requestor.cisco_cco_id}",
                403,
            )

        db_extension_query = (
            select(
                func.count(V2BookingContractsExtensions.booking_contract).label(
                    "extended_count"
                ),
                func.max(V2BookingContractsExtensions.extension_end_date).label(
                    "latest_extension"
                ),
            )
            .where(V2BookingContractsExtensions.booking_contract == booking_contract)
            .where(V2BookingContractsExtensions.is_deleted == "F")
            .group_by(V2BookingContractsExtensions.booking_contract)
        )

        db_extension = self.session.exec(db_extension_query).one_or_none()
        if (
            db_extension is not None
            and db_extension.extended_count >= extension_count_limit
        ):
            raise ServiceException(
                f"Booking Contract {booking_contract} has reached the extension limit",
                409,
            )

        day_delta = timedelta(days=duration_days)

        current_end_date = (
            max(db_booking.agreement_end_date, db_extension.latest_extension)
            if db_extension
            else db_booking.agreement_end_date
        )

        extension_end_date = current_end_date + day_delta

        if extension_end_date < db_booking.agreement_end_date:
            raise ServiceException(
                f"End date {extension_end_date} is before current end date {db_booking.agreement_end_date}",
                400,
            )

        db_extension = V2BookingContractsExtensions(
            booking_contract=booking_contract,
            extension_start_date=db_booking.agreement_end_date,
            extension_end_date=extension_end_date,
            created_by=requestor.cisco_cco_id,
        )

        self.session.add(db_extension)
        self.session.commit()
        return db_extension

    def update_booking_allocation_ratios(
        self,
        booking_contract: int,
        requestor: "V2User",
        allocation_fte_sw_ratio: Decimal,
        allocation_fte_hw_ratio: Decimal,
    ):
        from api.v2.orm import V2BookingContracts

        if any(
            (
                allocation_fte_sw_ratio < Decimal("0"),
                allocation_fte_hw_ratio < Decimal("0"),
            )
        ):
            raise ServiceException("Allocation ratios must be positive", 400)
        if any(
            (
                allocation_fte_sw_ratio > Decimal("1"),
                allocation_fte_hw_ratio > Decimal("1"),
            )
        ):
            raise ServiceException(
                "Allocation ratios must be less than or equal to 1", 400
            )
        if allocation_fte_sw_ratio + allocation_fte_hw_ratio > Decimal("1"):
            raise ServiceException(
                "Allocation ratios must sum to less than or equal to 1", 400
            )

        db_booking_query = self._db_booking_query(booking_contract).options(
            load_only(
                V2BookingContracts.booking_contract,
                V2BookingContracts.claimed_and_managed_by,
                V2BookingContracts.agreement_end_date,
                V2BookingContracts.booked_hw,
                V2BookingContracts.booked_sw,
                V2BookingContracts.allocation_fte_hw_ratio,
                V2BookingContracts.allocation_fte_sw_ratio,
            )
        )
        db_booking = self.session.exec(db_booking_query).one_or_none()
        if not db_booking:
            raise ServiceException(
                f"Booking Contract {booking_contract} not found", 404
            )
        if db_booking.claimed_and_managed_by != requestor.user_id:
            raise ServiceException(
                f"Booking Contract {booking_contract} is not claimed by user {requestor.cisco_cco_id}",
                403,
            )

        match db_booking.allocation_fte_hw_ratio, db_booking.allocation_fte_sw_ratio:
            case None, None:
                db_ratio_hw = Decimal("0.0")
                db_ratio_sw = Decimal("0.0")
            case Decimal(), Decimal():
                db_ratio_hw = db_booking.allocation_fte_hw_ratio
                db_ratio_sw = db_booking.allocation_fte_sw_ratio
            case Decimal(), None:
                db_ratio_hw = db_booking.allocation_fte_hw_ratio
                db_ratio_sw = Decimal("1.0") - db_ratio_hw
            case None, Decimal():
                db_ratio_sw = db_booking.allocation_fte_sw_ratio
                db_ratio_hw = Decimal("1.0") - db_ratio_sw
            case _:
                raise ServiceException(msg="Logic Error, Unhandled Case", code=500)

        total_allocation = Decimal(str(db_booking.booked_hw)) + Decimal(
            str(db_booking.booked_sw)
        )
        proposed_booked_hw = total_allocation * allocation_fte_hw_ratio
        proposed_booked_sw = total_allocation - proposed_booked_hw

        actual_hw_ratio = allocation_fte_hw_ratio
        actual_sw_ratio = Decimal("1.0") - allocation_fte_hw_ratio

        if actual_hw_ratio + actual_sw_ratio != Decimal("1.0"):
            raise ServiceException(
                f"Actual Allocations {actual_hw_ratio} + {actual_sw_ratio} do not sum to 1",
                500,
            )

        if proposed_booked_hw + proposed_booked_sw != total_allocation:
            raise ServiceException(
                f"Proposed Allocations {proposed_booked_hw} + {proposed_booked_sw} do not sum to total allocation {total_allocation}",
                500,
            )

        stmt = text(
            """
            UPDATE DC_BOOKINGS_CONTRACTS
            SET ALLOCATION_FTE_HW_RATIO = :actual_hw_ratio,
            ALLOCATION_FTE_SW_RATIO = :actual_sw_ratio,
            UPDATED_BY = :requestor,
            UPDATE_DTM = CURRENT_TIMESTAMP,
            SOLD_AS_HW_ALLOCATION = :proposed_booked_hw,
            SOLD_AS_SW_ALLOCATION = :proposed_booked_sw
            WHERE BOOKING_CONTRACT = :booking_contract
            AND IS_DELETED = 'F'
            """
        ).bindparams(
            booking_contract=booking_contract,
            actual_hw_ratio=actual_hw_ratio,
            actual_sw_ratio=actual_sw_ratio,
            requestor=requestor.cisco_cco_id,
            proposed_booked_hw=proposed_booked_hw,
            proposed_booked_sw=proposed_booked_sw,
        )
        self.session.execute(stmt)

    def _query_booking_contract_memberships(self, booking_contracts: list[int]):
        """Build query for check that booking contract exists."""
        from api.v2.orm import V2BookingContracts
        from api.v2.queries import QueryMembership

        query = (
            QueryMembership()
            .add_orm_membership(V2BookingContracts, booking_contracts)
            .build()
        )
        return query

    def _db_booking_query(self, booking_contract):
        from api.v2.orm import V2BookingContracts

        db_booking_query = (
            select(V2BookingContracts)
            .where(V2BookingContracts.booking_contract == booking_contract)
            .where(V2BookingContracts.is_deleted == "F")
        )
        return db_booking_query

    def _parse_service_type(self, sold_as_service_name: str) -> ServiceTypeFlag:
        match sold_as_service_name:
            case str(x) if x == "UNKNOWN" or x.endswith("(HW/SW)"):
                return ServiceTypeFlag.HW_SW
            case str(x) if x.endswith("(HW)"):
                return ServiceTypeFlag.HW
            case str(x) if x.endswith("(SW)"):
                return ServiceTypeFlag.SW
            case _:
                raise ServiceException(
                    "Unknown service type",
                    500,
                )

    def _get_booking_service_type(self, booking_contract) -> ServiceTypeFlag:
        from api.v2.orm import (
            V2BookingContracts,
            V2ServicePlans,
        )

        query_booking = (
            select(
                V2BookingContracts.booking_contract,
                V2BookingContracts.sold_as_service_type_id,
            )
            .where(V2BookingContracts.booking_contract == booking_contract)
            .where(V2BookingContracts.is_deleted == "F")
            .join(
                V2ServicePlans,
                and_(
                    V2ServicePlans.service_type_id
                    == V2BookingContracts.sold_as_service_type_id,
                    V2ServicePlans.is_deleted == "F",
                ),
            )
        )

        db_booking = self.session.exec(query_booking).one_or_none()
        if not db_booking:
            raise ServiceException(
                f"Booking Contract {booking_contract} not found", 404
            )

        return self.service_type_map[db_booking.sold_as_service_type_id]

    @classmethod
    def _validate_assignments(
        cls,
        assignments: list["V2BookingEngagementAssignment"],
        primary_role_id: int,
        service_type_flag: ServiceTypeFlag,
    ) -> None:
        """
        Validate the assignments to ensure they are well-formed.
        This includes checking for duplicate user and engagement pairs.
        """

        def get_assignment_key(
            assignment: "V2BookingEngagementAssignment",
        ) -> tuple[int, int]:
            return (assignment.dc_engagement_id, assignment.service_role_id)

        eng_primary_counts: defaultdict[tuple[int, int], int] = defaultdict(lambda: 0)
        for assignment in assignments:
            key = get_assignment_key(assignment)
            eng_primary_counts[key] += 1

        invalid_roles = [
            ((engagement_id, role_id), count)
            for (engagement_id, role_id), count in eng_primary_counts.items()
            if role_id == primary_role_id and count > 1
        ]

        if invalid_roles:
            logger.error(
                "These assignments have more than one Primary-CAM role per engagement: %s",
                invalid_roles,
            )
            raise ServiceException(
                "Please select exactly one Primary-CAM role per engagement", 400
            )

        allocation_sw: list[Decimal] = [
            assignment.sub_allocation_sw for assignment in assignments
        ]
        allocation_hw: list[Decimal] = [
            assignment.sub_allocation_hw for assignment in assignments
        ]
        sw_valid = sum(allocation_sw) == Decimal("1.0")
        hw_valid = sum(allocation_hw) == Decimal("1.0")

        match service_type_flag:
            case ServiceTypeFlag.HW_SW:
                if not all((hw_valid, sw_valid)):
                    raise ServiceException(
                        f"HW and SW allocations must sum to 1.0, Received HW={sum(allocation_hw)}, SW={sum(allocation_sw)}",
                        400,
                    )
            case ServiceTypeFlag.HW:
                if not hw_valid:
                    raise ServiceException(
                        f"HW allocations must sum to 1.0, Received HW={sum(allocation_hw)}",
                        400,
                    )
            case ServiceTypeFlag.SW:
                if not sw_valid:
                    raise ServiceException(
                        f"SW allocations must sum to 1.0, Received SW={sum(allocation_sw)}",
                        400,
                    )

        # A booking is one to many with engagements
        # A booking is one to many with users
        # A booking user is one to one with engagements (Can't have a user associated with 2+ engagements)
        user_ids = [
            (assignment.dc_user_id, assignment.dc_engagement_id)
            for assignment in assignments
        ]
        if len(user_ids) != len(set(user_ids)):
            raise ServiceException("Duplicate user and engagement assignments", 400)

    def _is_cxea_scale_booking(self, booking_contract: int) -> bool:
        """
        Check if a booking contract is CXEA Scale by examining its buying program name.
        """
        stmt = (
            text(
                """ 
            SELECT NVL(BUYING_PROGRAM_NAME ILIKE '%CXEA - Scale%', FALSE) AS IS_CXEA
                   FROM DC_BOOKINGS_CONTRACTS BC
                   LEFT JOIN DC_BUYING_PROGRAMS BUY ON BC.BUYING_PROGRAM_TYPE_ID = BUY.BUYING_PROGRAM_TYPE_ID
                   WHERE BC.BOOKING_CONTRACT = :booking_contract
                   LIMIT 1
            """
            )
            .bindparams(
                booking_contract=booking_contract,
            )
            .columns(is_cxea=Boolean)
        )

        result = self.session.exec(stmt).scalar_one()
        if result is None:
            raise ServiceException(
                f"Booking Contract {booking_contract} not found", 404
            )
        return result

    def _store_booking_override(
        self,
        booking_contract: int,
        booking_override_reason_id: int,
        requestor: "V2User",
    ):
        """Tracking special case for CXEA - Designated"""
        stmt = text(
            """
            INSERT INTO DC_BOOKING_OVERRIDE
            (BOOKING_CONTRACT, BOOKING_OVERRIDE_REASON_ID, CREATED_BY, CREATE_DTM, IS_DELETED)
            VALUES
            (:booking_contract, :booking_override_reason_id, :created_by, CURRENT_TIMESTAMP, 'F')
            """
        ).bindparams(
            booking_contract=booking_contract,
            booking_override_reason_id=booking_override_reason_id,
            created_by=requestor.cisco_cco_id,
        )
        self.session.execute(stmt)
