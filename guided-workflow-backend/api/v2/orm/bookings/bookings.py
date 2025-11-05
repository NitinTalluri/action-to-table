from datetime import date
from decimal import Decimal

from dateutil import relativedelta
from sqlalchemy import (
    Column,
    Date,
    Float,
    ForeignKey,
    Integer,
    Sequence,
    String,
    Table,
    func,
)
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import (
    Mapped,
    column_property,
    mapped_column,
    query_expression,
    relationship,
)

from api.v2.models import BookingContractType
from api.v2.orm import PyDecimal, V2Disengagement, V2Engagement

from ..json_varchar import JSONVarchar
from . import V2MetadataBase

"""
For Booking Contracts, we have one table but different expectations for what should be returned.
Doing this manually was cumbersome and error prone. We have different classes that use booking contracts as their table source
but we can define column_properties and relationships without affecting other classes that use the same table.
"""

booking_contracts_table = Table(
    "dc_bookings_contracts",
    V2MetadataBase.metadata,
    Column("booking_contract", Integer, primary_key=True),
    Column("created_by", String(255)),
    Column("create_dtm", Date, server_default=func.current_date()),
    Column("update_dtm", Date, server_default=func.current_date()),
    Column("updated_by", String(255)),
    Column("is_deleted", String(1), default="F"),
    Column("account_name", String(1000)),
    Column("booked_sav_1", String(1000)),
    Column("booked_sav_2", String(1000)),
    Column("booked_sav_3", String(1000)),
    Column(
        "booked_theater_id", Integer, ForeignKey("dc_theater.theater_id"), default=1
    ),
    Column(
        "sold_as_service_type_id",
        Integer,
        ForeignKey("dc_sold_as_service_types.service_type_id"),
        default=1,
    ),
    Column(
        "sold_as_pricing_type_id",
        Integer,
        ForeignKey("dc_pricing_model.pricing_type_id"),
        default=1,
    ),
    Column(
        "buying_program_type_id",
        Integer,
        ForeignKey("dc_buying_programs.buying_program_type_id"),
        default=1,
    ),
    Column(
        "booking_contract_type_id",
        Integer,
        ForeignKey("dc_typ_booking_type.id"),
        default=1,
    ),
    Column("booked_usd", Float, default=0),
    Column("agreement_start_date", Date, server_default=func.current_date()),
    Column("agreement_end_date", Date, server_default=func.current_date()),
    Column("booking_country", String(100), default=None),
    Column("cam_revenue_usd", Float, default=0),
    Column("cam_cost_usd", Float, default=0),
    Column("souced_allocation", Float, default=None),
    Column("quote_for_audit", String(1 << 16), default=None),
    Column("booked_date", Date, default=None),
    Column("sold_as_sw_allocation", Float, default=0),
    Column("sold_as_hw_allocation", Float, default=0),
    Column("ib_calc_sw_allocation", Float, default=0),
    Column("ib_calc_hw_allocation", Float, default=0),
    Column("claimed_and_managed_by", Integer, ForeignKey("dc_users.user_id")),
    Column("derived_new_renew", String, default=None),
    Column("allocation_fte_hw_ratio", PyDecimal, default=Decimal("0")),
    Column("allocation_fte_sw_ratio", PyDecimal, default=Decimal("0")),
    Column("dc_engagement_id_default", Integer, default=None),
    Column("sales_level_id", Integer, default=0),
)


class V2BookingContractType(V2MetadataBase):
    __tablename__ = "dc_typ_booking_type"

    id: Mapped[int] = mapped_column(
        Integer,
        autoincrement=True,
        primary_key=True,
    )
    value: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    extra = Column(
        JSONVarchar, default='{"is_prospective": true, "is_budgeted": false}'
    )

    @hybrid_property
    def is_prospective(self):
        return self.extra.get("is_prospective", True)

    @is_prospective.expression
    def is_prospective(cls):
        return (
            func.nvl(func.get_path(func.parse_json(cls.extra), "is_prospective"), False)
            == True
        )

    @hybrid_property
    def is_budgeted(self):
        return self.extra.get("is_budgeted", False)

    @is_budgeted.expression
    def is_budgeted(cls):
        return (
            func.nvl(func.get_path(func.parse_json(cls.extra), "is_budgeted"), False)
            == True
        )


class V2BookingContracts(V2MetadataBase):
    __table__ = booking_contracts_table
    __mapper_args__ = {
        "primary_key": booking_contracts_table.c.booking_contract,
        "exclude_properties": [
            "souced_allocation",
            "ib_calc_sw_allocation",
            "ib_calc_hw_allocation",
            "derived_new_renew",
        ],
    }

    allocation_fte_hw_ratio = column_property(
        (booking_contracts_table.c.allocation_fte_hw_ratio).label(
            "allocation_fte_hw_ratio"
        )
    )

    allocation_fte_sw_ratio = column_property(
        (booking_contracts_table.c.allocation_fte_sw_ratio).label(
            "allocation_fte_sw_ratio"
        )
    )

    is_virtual = column_property(
        (booking_contracts_table.c.booking_contract < 0).label("is_virtual")
    )
    booked_sw = column_property(
        func.nvl(booking_contracts_table.c.sold_as_sw_allocation, 0).label("booked_sw")
    )
    booked_hw = column_property(
        func.nvl(booking_contracts_table.c.sold_as_hw_allocation, 0).label("booked_hw")
    )
    calculated_sw = column_property(
        func.nvl(booking_contracts_table.c.ib_calc_sw_allocation, 0).label(
            "calculated_sw"
        )
    )
    calculated_hw = column_property(
        func.nvl(booking_contracts_table.c.ib_calc_hw_allocation, 0).label(
            "calculated_hw"
        )
    )
    sourced_allocation = column_property(
        func.nvl(booking_contracts_table.c.souced_allocation, 0).label(
            "sourced_allocation"
        )
    )
    derived_new_renew = column_property(
        func.iff(
            booking_contracts_table.c.derived_new_renew.in_(
                [v.value for v in BookingContractType]
            ),
            booking_contracts_table.c.derived_new_renew,
            None,
        ).label("derived_new_renew")
    )

    disengagement = relationship(
        "V2Disengagement",
        primaryjoin="and_(V2Disengagement.booking_contract==V2BookingContracts.booking_contract, "
        "V2Disengagement.is_deleted == 'F')",
        viewonly=True,
        uselist=False,
    )

    extensions = relationship(
        "V2BookingContractsExtensions",
        primaryjoin="and_(V2BookingContractsExtensions.booking_contract==V2BookingContracts.booking_contract, "
        "V2BookingContractsExtensions.is_deleted == 'F')",
        viewonly=True,
    )

    renewed_from = (
        query_expression()
    )  # This should be provided in query as cte or similar

    extended_count = (
        query_expression()
    )  # This should be provided in query as cte or similar

    engagement_name = query_expression(V2Engagement.engagement_name)

    is_disengaged = column_property(
        V2Disengagement.booking_contract.isnot(None).label("is_disengaged")
    )


class V2BookingContractsFinancialAdmin(V2MetadataBase):
    __table__ = booking_contracts_table
    __mapper_args__ = {
        "primary_key": booking_contracts_table.c.booking_contract,
        "exclude_properties": [
            "souced_allocation",
            "derived_new_renew",
            "dc_engagement_id_default",
        ],
    }

    assignments = relationship(
        "V2BookingResponsibleUsers",
        primaryjoin="and_("
        "V2BookingContracts.is_deleted=='F',"
        "V2BookingContracts.booking_contract=="
        "V2BookingResponsibleUsers.booking_contract,"
        " V2BookingResponsibleUsers.is_deleted=='F')",
    )

    @hybrid_property
    def is_virtual(self):
        return self.booking_contract < 0

    @is_virtual.expression
    def is_virtual(cls):
        return cls.booking_contract < 0

    @hybrid_property
    def is_verified(self):
        return self.update_dtm is not None

    @is_verified.expression
    def is_verified(cls):
        return cls.update_dtm.isnot(None)

    @is_verified.setter
    def is_verified(self, value):
        raise AttributeError("is_verified is read-only")

    @hybrid_property
    def is_current_and_unassigned(self):
        # No assignments and the current_timestamp > 30 days after the agreement_end_date
        is_current = (
            self.agreement_end_date + relativedelta.relativedelta(days=30)
            > date.today()
        )
        # noinspection PyTypeChecker,PydanticTypeChecker
        is_unassigned = len(self.assignments) == 0
        return all((is_current, is_unassigned))

    @hybrid_property
    def calculated_sw(self):
        return self.ib_calc_sw_allocation or 0

    @calculated_sw.expression
    def calculated_sw(cls):
        return func.nvl(cls.ib_calc_sw_allocation, 0)

    @calculated_sw.setter
    def calculated_sw(self, value):
        self.ib_calc_sw_allocation = value

    @hybrid_property
    def calculated_hw(self):
        return self.ib_calc_hw_allocation or 0

    @calculated_hw.expression
    def calculated_hw(cls):
        return func.nvl(cls.ib_calc_hw_allocation, 0)

    @calculated_hw.setter
    def calculated_hw(self, value):
        self.ib_calc_hw_allocation = value

    is_renewal = query_expression()

    booked_sw = column_property(
        func.nvl(booking_contracts_table.c.sold_as_sw_allocation, 0).label("booked_sw")
    )
    booked_hw = column_property(
        func.nvl(booking_contracts_table.c.sold_as_hw_allocation, 0).label("booked_hw")
    )


ProspectiveBookingSequence = Sequence("seq_dc_synthetic_bookings")


__all__ = [
    "ProspectiveBookingSequence",
    "V2BookingContractType",
    "V2BookingContracts",
    "V2BookingContractsFinancialAdmin",
    "booking_contracts_table",
]
