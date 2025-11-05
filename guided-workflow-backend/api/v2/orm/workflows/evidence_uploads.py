import datetime

from sqlalchemy import Date, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .. import V2MetadataBase


class V2EvidenceCustomerHdr(V2MetadataBase):
    __tablename__ = "dc_evidence_customer_hdr"
    request_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    effective_date: Mapped[datetime.date] = mapped_column(Date)
    source: Mapped[str] = mapped_column(String)
    note: Mapped[str] = mapped_column(String)
    dc_engagement_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("dc_engagement_hdr.dc_engagement_id")
    )
    file_name_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("dc_user_defined_type.id")
    )


class V2EvidenceCollectorHdr(V2MetadataBase):
    __tablename__ = "dc_evidence_collector_hdr"
    request_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    effective_date: Mapped[datetime.date] = mapped_column(Date)
    source: Mapped[str] = mapped_column(String)
    note: Mapped[str] = mapped_column(String)
    dc_engagement_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("dc_engagement_hdr.dc_engagement_id")
    )
    file_name_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("dc_user_defined_type.id")
    )
