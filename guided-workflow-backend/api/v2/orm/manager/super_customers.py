from sqlalchemy import (
    ForeignKey,
    Integer,
    PrimaryKeyConstraint,
    Sequence,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from . import V2MetadataBase


class V2SuperCustomer(V2MetadataBase):
    __tablename__ = "dc_super_customer"
    super_customer_id: Mapped[int] = mapped_column(
        Integer, Sequence("seq_dc_generic"), primary_key=True
    )
    super_customer_name: Mapped[str] = mapped_column(String(1 << 16), nullable=False)

    __table_args__ = (UniqueConstraint("super_customer_name"),)


class V2SuperCustomerEngagements(V2MetadataBase):
    __tablename__ = "dc_super_customer_engagements"
    super_customer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("dc_super_customer.super_customer_id"), nullable=False
    )
    dc_engagement_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("dc_engagement_hdr.dc_engagement_id"), nullable=False
    )

    __table_args__ = (
        PrimaryKeyConstraint("super_customer_id", "dc_engagement_id"),
        UniqueConstraint("dc_engagement_id"),
    )


__all__ = [
    "V2SuperCustomer",
    "V2SuperCustomerEngagements",
]
