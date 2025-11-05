import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import JSONVarchar, V2MetadataBase

if TYPE_CHECKING:
    from sqlmodel import Session

    from ..models import V2ContractCreate, V2ManagedContractCreate


class V2AssetMgtType(V2MetadataBase):
    __tablename__ = "dc_contract_asset_mgt_types"
    am_type_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    asset_management_type: Mapped[str] = mapped_column(String(1 << 16))
    contracts = relationship("V2Contract", viewonly=True)


class V2MonitorType(V2MetadataBase):
    __tablename__ = "dc_contract_monitor_types"
    monitor_type_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    monitor_reason: Mapped[str] = mapped_column(String(1 << 16))
    contracts = relationship("V2Contract", viewonly=True)


class V2ContractType(V2MetadataBase):
    __tablename__ = "dc_contract_types"
    contract_type_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    service_contract_type: Mapped[str] = mapped_column(String(1 << 16))
    contracts = relationship("V2Contract", viewonly=True)


class V2Contract(V2MetadataBase):
    __tablename__ = "dc_engagement_contracts"
    contract_number: Mapped[int] = mapped_column(
        Integer, primary_key=True, default=None
    )
    dc_engagement_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("dc_engagement_hdr.dc_engagement_id"), primary_key=True
    )
    booking_contract: Mapped[str] = mapped_column(String, default="")
    cams: Mapped[str] = mapped_column(String, default="")
    am_start_date: Mapped[datetime.datetime | None] = mapped_column(
        DateTime, default=None
    )
    am_end_date: Mapped[datetime.datetime | None] = mapped_column(
        DateTime, default=None
    )
    allowed_service_levels: Mapped[str] = mapped_column(String, default="")
    service_contract_type_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("dc_contract_types.contract_type_id"), default=1
    )
    asset_management_type_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("dc_contract_asset_mgt_types.am_type_id"), default=1
    )
    monitor_reason_type_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("dc_contract_monitor_types.monitor_type_id"), default=1
    )
    #####
    engagement = relationship("V2Engagement", back_populates="contracts", viewonly=True)
    monitor_type = relationship(
        "V2MonitorType", back_populates="contracts", viewonly=True
    )
    service_contract_type = relationship(
        "V2ContractType", back_populates="contracts", viewonly=True
    )
    asset_management_type = relationship(
        "V2AssetMgtType", back_populates="contracts", viewonly=True
    )

    @classmethod
    def create_from_model(
        cls, model: "V2ContractCreate", logged_user: str, session: "Session"
    ):
        return super().create_from_model(model, logged_user, session)


########################################################################################################################


class V2ServicePlans(V2MetadataBase):
    __tablename__ = "dc_sold_as_service_types"
    service_type_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sold_as_service_name: Mapped[str] = mapped_column(String(1 << 16))


class V2BuyingPrograms(V2MetadataBase):
    __tablename__ = "dc_buying_programs"
    buying_program_type_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    buying_program_name: Mapped[str] = mapped_column(String(1 << 16))
    extra = Column(JSONVarchar, default='{"is_default": false}')


class V2Theater(V2MetadataBase):
    __tablename__ = "dc_theater"
    theater_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    theater_name: Mapped[str] = mapped_column(String(1 << 16))


class V2ManagedContracts(V2MetadataBase):
    __tablename__ = "dc_managed_service_contracts"
    contract_number: Mapped[int] = mapped_column(Integer, primary_key=True)
    booking_contract: Mapped[int] = mapped_column(
        Integer, ForeignKey("dc_bookings_contracts.booking_contract"), primary_key=True
    )
    dc_user_id: Mapped[int] = mapped_column(
        ForeignKey("dc_users.user_id"), primary_key=True
    )
    dc_engagement_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("dc_engagement_hdr.dc_engagement_id"), primary_key=True
    )
    allowed_service_levels: Mapped[str] = mapped_column(String, default="")
    contract_name: Mapped[str] = mapped_column(String, default="")
    notes: Mapped[str] = mapped_column(String, default="")

    def create_from_model(
        cls, model: "V2ManagedContractCreate", logged_user: str, session: "Session"
    ):
        return super().create_from_model(model, logged_user, session)


class V2MonitorContracts(V2MetadataBase):
    __tablename__ = "dc_monitor_service_contracts"
    contract_number: Mapped[int] = mapped_column(Integer, primary_key=True)
    monitor_type_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("dc_contract_monitor_types.monitor_type_id"), default=1
    )
    dc_engagement_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("dc_engagement_hdr.dc_engagement_id"), primary_key=True
    )
    monitor_notes: Mapped[str | None] = mapped_column(String, default=None)


class V2PricingModel(V2MetadataBase):
    __tablename__ = "dc_pricing_model"
    pricing_type_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pricing_model_name: Mapped[str] = mapped_column(String)


__all__ = [
    "V2AssetMgtType",
    "V2BuyingPrograms",
    "V2Contract",
    "V2ContractType",
    "V2ManagedContracts",
    "V2MonitorContracts",
    "V2MonitorType",
    "V2PricingModel",
    "V2ServicePlans",
    "V2Theater",
]
