import datetime
import logging
import re
from datetime import date
from typing import Any, Optional

from pydantic.v1 import Field, validator

from api.v2.models import Model, parse_currency, try_process_date
from api.v2.models.base import BatchifyMixin

logger = logging.getLogger("api")


class V2RevenueCXEAEntry(Model):
    class Config:
        orm_mode = True
        use_enum_values = True
        anystr_max_length = 1 << 16
        anystr_strip_whitespace = True

    fiscal_period_id: Optional[str] = Field(None, description="Fiscal Period ID")
    fiscal_year: Optional[int] = Field(None, description="Fiscal Year")
    fiscal_quarter_id: Optional[str] = Field(None, description="Fiscal Quarter ID")
    sales_level_1: Optional[str] = Field(None, description="Sales Level 1")
    sales_level_2: Optional[str] = Field(None, description="Sales Level 2")
    sales_level_3: Optional[str] = Field(None, description="Sales Level 3")
    finance_sub_group_or_contract_type: Optional[str] = Field(
        None, description="Finance Sub Group or Contract Type"
    )
    mktg_part_id: Optional[str] = Field(None, description="Marketing Part ID")
    finance_bu_or_service_category: Optional[str] = Field(
        None, description="Finance BU or Service Category"
    )
    subscription_id: Optional[str] = Field(
        None, description="Subscription Reference Id"
    )
    contract_number: Optional[int] = Field(None, description="Contract Number")
    transaction_number: Optional[int] = Field(None, description="Transaction Number")
    transaction_type: Optional[str] = Field(None, description="Transaction Type")
    transaction_date: Optional[date] = Field(None, description="Transaction Date")
    contract_start_date: Optional[date] = Field(None, description="Contract Start Date")
    contract_end_date: Optional[date] = Field(None, description="Contract End Date")
    contract_term: Optional[float] = Field(None, description="Contract Term")
    total_amount: Optional[float] = Field(None, description="Total Amount")
    end_customer_global_ultimate_name: Optional[str] = Field(
        None, description="End Customer Global Ultimate Name"
    )
    invoice_amount: Optional[float] = Field(None, description="Invoice Amount")
    invoice_revenue: Optional[float] = Field(None, description="Invoice Revenue")

    country: Optional[str] = Field(None, description="Country")
    l1_sales_finance_hierarchy_code: Optional[str] = Field(
        None, description="L1 Sales Finance Hierarchy Code"
    )
    l2_sales_finance_hierarchy_code: Optional[str] = Field(
        None, description="L2 Sales Finance Hierarchy Code"
    )
    external_theater_name_l1: Optional[str] = Field(
        None, description="External Theater Name L1"
    )
    subscription_code: Optional[str] = Field(None, description="Subscription Code")

    # validators
    _parse_dates = validator(
        "transaction_date",
        "contract_start_date",
        "contract_end_date",
        allow_reuse=True,
        pre=True,
    )(try_process_date)


class V2RevenueCXEAStoredProcParams(BatchifyMixin[V2RevenueCXEAEntry]):
    __root__: list[V2RevenueCXEAEntry]


class V2RevenueCXEAResponse(Model):
    count: int = Field(..., description="Count")


class V2RevenueHTECEntry(Model):
    class Config:
        orm_mode = True
        use_enum_values = True
        anystr_max_length = 1 << 16
        anystr_strip_whitespace = True

    fiscal_period_id: Optional[str] = Field(None, description="Fiscal Period ID")
    fiscal_year: Optional[int] = Field(None, description="Fiscal Year")
    fiscal_quarter_id: Optional[str] = Field(None, description="Fiscal Quarter ID")
    sales_level_1: Optional[str] = Field(None, description="Sales Level 1")
    sales_level_2: Optional[str] = Field(None, description="Sales Level 2")
    sales_level_3: Optional[str] = Field(None, description="Sales Level 3")
    finance_sub_group_or_contract_type: str = Field(
        None, description="Finance Sub Group or Contract Type"
    )
    mktg_part_id: Optional[str] = Field(None, description="Marketing Part ID")
    finance_bu_or_service_category: Optional[str] = Field(
        None, description="Finance BU or Service Category"
    )
    contract_number: Optional[int] = Field(None, description="Contract Number")
    transaction_number: Optional[int] = Field(None, description="Transaction Number")
    transaction_type: Optional[str] = Field(None, description="Transaction Type")
    transaction_date: Optional[date] = Field(None, description="Transaction Date")
    contract_start_date: Optional[date] = Field(None, description="Contract Start Date")
    contract_end_date: Optional[date] = Field(None, description="Contract End Date")
    contract_term: Optional[float] = Field(None, description="Contract Term")
    total_amount: Optional[float] = Field(None, description="Total Amount")

    _parse_dates = validator(
        "transaction_date",
        "contract_start_date",
        "contract_end_date",
        allow_reuse=True,
        pre=True,
    )(try_process_date)


class V2RevenueHTECStoredProcParams(BatchifyMixin[V2RevenueHTECEntry]):
    __root__: list[V2RevenueHTECEntry]


class V2RevenueHTECResponse(V2RevenueCXEAResponse): ...


class V2RevenueCOGSEntry(Model):
    company: Optional[str] = Field(...)
    department: Optional[str] = Field(...)
    department_name: Optional[str] = Field(...)
    account: Optional[str] = Field(...)
    account_description: Optional[str] = Field(...)
    sub_account: Optional[str] = Field(...)
    sub_account_description: Optional[str] = Field(...)
    project: Optional[str] = Field(...)
    market_segment: Optional[str] = Field(...)
    fiscal_period: Optional[str] = Field(...)
    gl_je_number: Optional[str] = Field(...)
    gl_je_line_number: Optional[str] = Field(...)
    source: Optional[str] = Field(...)
    category: Optional[str] = Field(...)
    batch_name: Optional[str] = Field(...)
    gl_description: Optional[str] = Field(...)
    gl_date: Optional[str] = Field(...)
    invoice_ap_gl_date: Optional[str] = Field(...)
    invoice_ap_date: Optional[str] = Field(...)
    invoice: Optional[str] = Field(...)
    invoice_description: Optional[str] = Field(...)
    ban_id: Optional[str] = Field(...)
    description: Optional[str] = Field(...)
    vendor: Optional[str] = Field(...)
    po_number: Optional[str] = Field(...)
    buyer: Optional[str] = Field(...)
    vendor_inv_distributor_key: Optional[str] = Field(...)
    person_entered_by: Optional[str] = Field(...)
    transactional_currency_code: Optional[str] = Field(...)
    trx_to_func_exchange_rate: Optional[float] = Field(...)
    transactional_currency_dr: Optional[float] = Field(...)
    transactional_currency_cr: Optional[float] = Field(...)
    transactional_currency_net: Optional[float] = Field(...)
    ap_transactional_currency_net: Optional[float] = Field(...)
    functional_currency_code: Optional[str] = Field(...)
    functional_currency_dr: Optional[float] = Field(...)
    functional_currency_cr: Optional[float] = Field(...)
    functional_currency_net: Optional[float] = Field(...)
    ap_functional_currency_net: Optional[float] = Field(...)
    usd_dr: Optional[float] = Field(...)
    usd_cr: Optional[float] = Field(...)
    usd_net: Optional[float] = Field(...)
    ap_usd_net: Optional[float] = Field(...)
    theater: Optional[str] = Field(...)
    category1: Optional[str] = Field(...)
    category2: Optional[str] = Field(...)
    fiscal_period_id: Optional[str] = Field(None, description="Fiscal Period ID")


class V2RevenueCOGSStoredProcParams(BatchifyMixin[V2RevenueCOGSEntry]):
    __root__: list[V2RevenueCOGSEntry]


class V2RevenueSEAEntry(Model):
    fmw_flag: str | None = Field(default=None, description="FMW Flag")
    web_order_id: str | None = Field(
        default=None,
        description="Web Order ID. Mostly numeric but may contain 'UNKNOWN'",
    )
    bp_name: str | None = Field(default=None, description="BP Name")
    sales_level_1: str | None = Field(default=None, description="Sales Level 1")
    sales_level_2: str | None = Field(default=None, description="Sales Level 2")
    sales_level_3: str | None = Field(default=None, description="Sales Level 3")
    end_customer_global_ultimate_name: str | None = Field(
        default=None, description="End Customer Global Ultimate Name"
    )
    end_customer_global_ultimate_id: str | None = Field(
        default=None, description="End Customer Global Ultimate ID"
    )
    ca_service_bookings_net: str | None = Field(
        default=None, description="CA Service Bookings Net (Currency)"
    )
    annual_bookings_net: str | None = Field(
        default=None, description="Annual Bookings Net (Currency)"
    )
    subscription_reference_id: str | None = Field(
        default=None, description="Subscription Reference ID"
    )
    date_booked: datetime.date | None = Field(default=None, description="Date Booked")

    _parse_currency = validator(
        "ca_service_bookings_net", "annual_bookings_net", pre=True, allow_reuse=True
    )(parse_currency)
    _parse_date = validator("date_booked", pre=True, allow_reuse=True)(try_process_date)

    @validator("subscription_reference_id", pre=True)
    def validate_subscription_reference_id(cls, v: Any) -> str | None:
        """
        Validate and clean the subscription reference id
        """
        match v:
            case int():
                return str(v)
            case str():
                s = re.sub("[^\\d]", "", v)
                return s if s else None
            case None:
                return None
            case _:
                msg = f"Invalid subscription reference id: type={type(v)} value={v}"
                logger.info(msg)
                return None


class V2RevenueSEAStoredProcParams(BatchifyMixin[V2RevenueSEAEntry]):
    __root__: list[V2RevenueSEAEntry]


class V2RevenueCOGSResponse(Model):
    count: int = Field(..., description="Count")
