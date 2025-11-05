import datetime

from sqlalchemy import Date, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ... import V2MetadataBase


class V2RevenueCXEA(V2MetadataBase):
    """
    Pydantic Model : V2RevenueCXEAEntry

    This data has no guarantees of uniqueness, or shape - so we are using a md5 hash of the data to ensure uniqueness

    """

    __tablename__ = "dc_revenue_cxea"
    fiscal_period_id: Mapped[str | None] = mapped_column(String)
    fiscal_year: Mapped[int | None] = mapped_column(Integer)
    fiscal_quarter_id: Mapped[str | None] = mapped_column(String)
    sales_level_1: Mapped[str | None] = mapped_column(String)
    sales_level_2: Mapped[str | None] = mapped_column(String)
    finance_sub_group_or_contract_type: Mapped[str | None] = mapped_column(String)
    mktg_part_id: Mapped[str | None] = mapped_column(String)
    finance_bu_or_service_category: Mapped[str | None] = mapped_column(String)
    contract_number: Mapped[int | None] = mapped_column(Integer)
    transaction_number: Mapped[int | None] = mapped_column(Integer)
    transaction_type: Mapped[str | None] = mapped_column(String)
    transaction_date: Mapped[datetime.date | None] = mapped_column(Date)
    contract_start_date: Mapped[datetime.date | None] = mapped_column(Date)
    contract_end_date: Mapped[datetime.date | None] = mapped_column(Date)
    contract_term: Mapped[int | None] = mapped_column(Integer)
    total_amount: Mapped[int | None] = mapped_column(Integer)
    # Note: md5_hash will only be generated in the stored_procedure
    md5_hash: Mapped[str] = mapped_column(String, primary_key=True)
