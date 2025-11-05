import datetime
from decimal import Decimal
from typing import Literal, Union

from pydantic.v1 import Field

from . import Model


class UserSDPConcreteTimeEntryDetailRow(Model):
    """
    This model represents a fully scoped time entry,
    which is a time entry that is scoped to a specific booking contract / engagement
    """

    entry_id: int | None = Field(
        None,
        description="The unique identifier for the time entry. If a user has previously submitted a time entry, this field will be populated with the entry_id of the existing time entry. Otherwise, it will be null.",
    )
    booking_contract: int
    dc_engagement_id: int
    dc_user_id: int
    deliverable_desc: str
    deliverable_id: int
    abstract_deliverable_id: Literal[None]
    engagement_name: str
    entry_date: datetime.date
    fiscal_year_number: int
    hours: float
    is_abstract: Literal[False] = Field(
        ...,
        description="Indicates if this time entry is abstract (false) or not (true). If true, the deliverable refers to the `dc_sdp_typ_abstract_deliverable` table, otherwise it refers to the `dc_sdp_deliverable` table.",
    )
    quarter: int
    week_num_in_year: int


class UserSDPConcreteTimeEntrySparseRow(Model):
    """
    A sparse version of UserSDPConcreteTimeEntryDetailRow for POST operations.
    """

    entry_id: int | None = Field(
        None,
        description="The unique identifier for the time entry. If a user has previously submitted a time entry, this field will be populated with the entry_id of the existing time entry. Otherwise, it will be null.",
    )
    booking_contract: int
    dc_engagement_id: int
    dc_user_id: int
    deliverable_id: int
    abstract_deliverable_id: Literal[None]
    entry_date: datetime.date
    hours: float
    is_abstract: Literal[False] = Field(
        ...,
        description="Indicates if this time entry is abstract (false) or not (true). If true, the deliverable refers to the `dc_sdp_typ_abstract_deliverable` table, otherwise it refers to the `dc_sdp_deliverable` table.",
    )


class UserSDPAbstractTimeEntryDetailRow(Model):
    entry_id: int | None = Field(
        None,
        description="The unique identifier for the time entry. If a user has previously submitted a time entry, this field will be populated with the entry_id of the existing time entry. Otherwise, it will be null.",
    )
    booking_contract: Literal[None]
    dc_engagement_id: Literal[None]
    dc_user_id: int
    deliverable_desc: str
    deliverable_id: Literal[None]
    abstract_deliverable_id: int
    engagement_name: Literal[None]
    entry_date: datetime.date
    fiscal_year_number: int
    hours: float
    is_abstract: Literal[True] = Field(
        ...,
        description="Indicates if this time entry is abstract (false) or not (true). If true, the deliverable refers to the `dc_sdp_typ_abstract_deliverable` table, otherwise it refers to the `dc_sdp_deliverable` table.",
    )
    quarter: int
    week_num_in_year: int


class UserSDPAbstractTimeEntrySparseRow(Model):
    """
    A sparse version of UserSDPAbstractTimeEntryDetailRow for POST operations.
    """

    entry_id: int | None = Field(
        None,
        description="The unique identifier for the time entry. If a user has previously submitted a time entry, this field will be populated with the entry_id of the existing time entry. Otherwise, it will be null.",
    )
    booking_contract: Literal[None]
    dc_engagement_id: Literal[None]
    dc_user_id: int
    deliverable_id: Literal[None]
    abstract_deliverable_id: int
    entry_date: datetime.date
    hours: float
    is_abstract: Literal[True] = Field(
        ...,
        description="Indicates if this time entry is abstract (false) or not (true). If true, the deliverable refers to the `dc_sdp_typ_abstract_deliverable` table, otherwise it refers to the `dc_sdp_deliverable` table.",
    )


class UserSDPTimeEntryDetailRow(Model):
    __root__: Union[
        UserSDPConcreteTimeEntryDetailRow, UserSDPAbstractTimeEntryDetailRow
    ] = Field(
        ...,
        description="A concrete or abstract time entry detail row",
        discriminator="is_abstract",
    )


class UserSDPTimeEntryDetail(Model):
    entries: list[UserSDPTimeEntryDetailRow] = Field(
        ...,
        description="The list of time entries (concrete or abstract) with full details",
    )


class UserSDPTimeEntrySparseRow(Model):
    """
    A sparse version of UserSDPTimeEntryDetailRow for POST operations.
    """

    __root__: Union[
        UserSDPConcreteTimeEntrySparseRow, UserSDPAbstractTimeEntrySparseRow
    ] = Field(
        ...,
        description="A concrete or abstract time entry sparse row",
        discriminator="is_abstract",
    )


class UserSDPTimeEntrySparse(Model):
    """
    A sparse version of UserSDPTimeEntryDetail for POST operations.
    """

    entries: list[UserSDPTimeEntrySparseRow] = Field(
        ...,
        description="The list of time entries (concrete or abstract) with sparse details",
    )


class UserSDPWeeklyIndex(Model):
    start_date: datetime.date = Field(
        None,
        description="The start date of the week. We consider Monday as the first day of the week.",
    )
    end_date: datetime.date = Field(
        None,
        description="The end date of the week. We consider Sunday as the last day of the week.",
    )
    fiscal_year_number: int
    quarter: int
    week_num_in_year: int
    year: int
    total_hours: Decimal = Field(
        Decimal("0.0"),
        description="The total number of hours submitted for the week.",
    )


__all__ = [
    "UserSDPAbstractTimeEntryDetailRow",
    "UserSDPAbstractTimeEntrySparseRow",
    "UserSDPConcreteTimeEntryDetailRow",
    "UserSDPConcreteTimeEntrySparseRow",
    "UserSDPTimeEntryDetail",
    "UserSDPTimeEntryDetailRow",
    "UserSDPTimeEntrySparse",
    "UserSDPTimeEntrySparseRow",
    "UserSDPWeeklyIndex",
]
