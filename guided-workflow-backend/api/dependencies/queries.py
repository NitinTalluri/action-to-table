import datetime
from collections import defaultdict
from functools import partial
from typing import (
    TYPE_CHECKING,
    Annotated,
    Callable,
    Literal,
    NamedTuple,
    Optional,
    TypedDict,
)
from zoneinfo import ZoneInfo

from fastapi import Depends, HTTPException, Path, Query
from pydantic.v1 import BaseModel
from sqlalchemy import literal, select, union_all
from starlette.status import HTTP_404_NOT_FOUND

from .database import GetSessionDep  # noqa: TC001
from .security import UserRequest  # noqa: TC001

if TYPE_CHECKING:
    from api.v2.models import TUiEnum
    from api.v2.orm import V2User


class GetReferencedReturn(NamedTuple):
    dc_engagement_id: int
    db_user: "V2User"


class EngagementBody(BaseModel):
    dc_engagement_id: int


def get_db_user(
    req: UserRequest, session: GetSessionDep, logged_user: Optional[str] = None
) -> "V2User":
    """
    Get the user that is referenced in the request. If logged_user is provided, it must be an admin user.
    This will be used to assume the role of the user in the request. If this is the case, avoid updating the session cookie.
    """
    from api.v2.orm import V2User

    session_cookie = req.session
    can_assume_role = req.user.is_admin or req.user.is_support
    is_assumed_role = (
        can_assume_role and logged_user is not None and logged_user != req.user.username
    )

    cookie_user_id = session_cookie.get("user_id")
    cookie_cisco_cco_id = session_cookie.get("cisco_cco_id")
    cookie_user_title = session_cookie.get("user_title")

    has_all_cookies = all((cookie_user_id, cookie_cisco_cco_id, cookie_user_title))

    match has_all_cookies, is_assumed_role:
        case (_, True):
            db_user = session.exec(
                select(V2User)
                .where(V2User.cisco_cco_id == logged_user)
                .where(V2User.is_deleted == "F")
            ).scalar_one_or_none()
            if db_user is None:
                raise HTTPException(
                    status_code=HTTP_404_NOT_FOUND, detail="User not found"
                )

            return db_user
        case (True, False):
            return V2User(
                user_id=cookie_user_id,
                cisco_cco_id=cookie_cisco_cco_id,
                user_title=cookie_user_title,
            )
        case (False, False):
            db_user = session.exec(
                select(V2User)
                .where(V2User.cisco_cco_id == req.user.username)
                .where(V2User.is_deleted == "F")
            ).scalar_one_or_none()
            if db_user is None:
                raise HTTPException(
                    status_code=HTTP_404_NOT_FOUND, detail="User not found"
                )
            session_cookie["user_id"] = db_user.user_id
            session_cookie["cisco_cco_id"] = db_user.cisco_cco_id
            session_cookie["user_title"] = db_user.user_title
            return db_user
        case _:
            raise ValueError("Invalid state")


GetUserDep = Annotated["V2User", Depends(get_db_user)]


def queried_action_items(session: GetSessionDep) -> dict["TUiEnum", int]:
    """Query all action items and return a dict of ui_enum to tree_id"""
    from api.v2.orm import V2ActionItem

    query = (select(V2ActionItem.tree_id, V2ActionItem.ui_enum)).where(
        (V2ActionItem.is_deleted == "F") & (V2ActionItem.ui_enum != None)
    )
    result = session.exec(query).all()
    return {row.ui_enum: row.tree_id for row in result}


ActionItemsDep = Annotated[dict["TUiEnum", int], Depends(queried_action_items)]


EngagementPath = Annotated[int, Path(title="dc_engagement_id")]


def authorized_engagement_path(
    db_user: GetUserDep, session: GetSessionDep, dc_engagement_id: EngagementPath
) -> GetReferencedReturn:
    """
    Given a user request and dc_engagement_id, return the engagement id and user if the user is authorized to perform the action
    otherwise raise an HTTPException
    """
    from api.v2.queries import query_referenced_engagement_id

    if dc_engagement_id is None:
        raise HTTPException(status_code=400, detail="dc_engagement_id must be provided")

    db_engagement_query = query_referenced_engagement_id(
        dc_engagement_id, db_user.user_id
    )
    db_engagement = session.exec(db_engagement_query).one_or_none()

    if not db_engagement:
        raise HTTPException(
            status_code=403, detail="Not authorized to perform this action"
        )

    return GetReferencedReturn(dc_engagement_id=dc_engagement_id, db_user=db_user)


AuthorizedEngagementPath = Annotated[
    GetReferencedReturn, Depends(authorized_engagement_path)
]


def authorized_engagement_body(
    db_user: GetUserDep, session: GetSessionDep, payload: EngagementBody
) -> GetReferencedReturn:
    from api.v2.queries import query_referenced_engagement_id

    dc_engagement_id = payload.dc_engagement_id
    db_engagement_query = query_referenced_engagement_id(
        dc_engagement_id, db_user.user_id
    )
    db_engagement = session.exec(db_engagement_query).one_or_none()

    if not db_engagement:
        raise HTTPException(
            status_code=403, detail="Not authorized to perform this action"
        )

    return GetReferencedReturn(dc_engagement_id=dc_engagement_id, db_user=db_user)


AuthorizedEngagementBody = Annotated[
    GetReferencedReturn, Depends(authorized_engagement_body)
]


def fetch_engagement_links(payload: EngagementBody, session: GetSessionDep):
    from api.v2.queries import get_engagement_links

    return get_engagement_links(
        dc_engagement_id=payload.dc_engagement_id, session=session
    )


def fetch_engagement_evidence_uploads(payload: EngagementBody, session: GetSessionDep):
    from api.v2.queries import get_evidence_uploads

    return get_evidence_uploads(
        dc_engagement_id=payload.dc_engagement_id, session=session
    )


TBookingTableTypeNames = Literal[
    "dc_bookings_user_role", "dc_sold_as_service_types", "dc_buying_programs"
]


class FetchBookingServiceTypeTableReturn(TypedDict):
    id: int
    value: str
    is_deleted: str


TFetchBookingServiceTypeTableReturn = dict[
    TBookingTableTypeNames, list[FetchBookingServiceTypeTableReturn]
]


def fetch_booking_service_types(
    session: GetSessionDep,
) -> TFetchBookingServiceTypeTableReturn:
    """
    The ManagerBookingsService requires a mapping of id: value for:
    - ``V2BookingsUserRole`` (dc_bookings_user_role)
    - ``V2ServicePlans`` (dc_sold_as_service_types)
    - ``V2BuyingPrograms`` (dc_buying_programs)
    """

    from api.v2.orm import V2BookingsUserRole, V2BuyingPrograms, V2ServicePlans

    select_bookings = select(
        literal("dc_bookings_user_role").label("table_name"),
        V2BookingsUserRole.bookings_role_id.label("id"),
        V2BookingsUserRole.bookings_role.label("value"),
        V2BookingsUserRole.is_deleted.label("is_deleted"),
    ).select_from(V2BookingsUserRole)
    select_service_plans = select(
        literal("dc_sold_as_service_types").label("table_name"),
        V2ServicePlans.service_type_id.label("id"),
        V2ServicePlans.sold_as_service_name.label("value"),
        V2ServicePlans.is_deleted.label("is_deleted"),
    ).select_from(V2ServicePlans)
    select_buying_programs = select(
        literal("dc_buying_programs").label("table_name"),
        V2BuyingPrograms.buying_program_type_id.label("id"),
        V2BuyingPrograms.buying_program_name.label("value"),
        V2BuyingPrograms.is_deleted.label("is_deleted"),
    ).select_from(V2BuyingPrograms)

    union_query = union_all(
        select_bookings, select_service_plans, select_buying_programs
    )
    rows = session.exec(union_query).mappings().all()
    results: TFetchBookingServiceTypeTableReturn = defaultdict(list)
    for row in rows:
        results[row.table_name].append(FetchBookingServiceTypeTableReturn(**row))
    return dict(results)


ManagerBookingsServiceTypesDep = Annotated[
    dict[TBookingTableTypeNames, list[FetchBookingServiceTypeTableReturn]],
    Depends(fetch_booking_service_types),
]


ISODateStringQuery = Annotated[
    str | None,
    Query(
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="ISO formatted date string (YYYY-MM-DD).",
    ),
]


class DateStringQuery:
    """
    When used as a dependency, this will return a datetime.date object from a query parameter
    called `date` that is expected to be an ISO formatted date string. If the query parameter
    is not provided, the default_func will be called to return the current date in UTC.
    """

    def __init__(self, default_func: Callable[[], datetime.date]):
        self.default_func = default_func

    def __call__(self, date: ISODateStringQuery = None) -> datetime.date:
        match date:
            case None:
                return self.default_func()
            case str():
                try:
                    return datetime.date.fromisoformat(date)
                except ValueError:
                    return self.default_func()
            case _:
                return self.default_func()


class DateRange(NamedTuple):
    start_date: datetime.date
    end_date: datetime.date


class DateStringRangeQuery:
    """
    When used as a dependency, this will return a tuple of datetime.date objects from two query parameters
    called `start_date` and `end_date` that are expected to be ISO formatted date strings. If the query parameters
    are not provided, the default_func will be called which should return a tuple of two dates.
    """

    def __init__(self, default_func: Callable[[], DateRange]):
        self.default_func = default_func

    def __call__(
        self, start_date: ISODateStringQuery = None, end_date: ISODateStringQuery = None
    ) -> DateRange:
        match start_date, end_date:
            case None, None:
                return self.default_func()
            case str(), str():
                try:
                    start = datetime.date.fromisoformat(start_date)
                    end = datetime.date.fromisoformat(end_date)
                    return DateRange(start, end)
                except ValueError:
                    return self.default_func()
            case _:
                return self.default_func()


def _get_current_date() -> datetime.date:
    return datetime.datetime.now(tz=ZoneInfo("UTC")).date()


def _get_current_date_range(offset: int) -> DateRange:
    """Using current date, return a delta of +/- 15 days"""
    offset_td = datetime.timedelta(offset)
    today = datetime.datetime.now(tz=ZoneInfo("UTC")).date()
    start_date = today - offset_td
    end_date = today + offset_td
    return DateRange(start_date=start_date, end_date=end_date)


current_date_string_query = DateStringQuery(default_func=_get_current_date)
CurrentDateParamDep = Annotated[datetime.date, Depends(current_date_string_query)]
get_7_day_range = partial(_get_current_date_range, offset=7)
current_date_range_query = DateStringRangeQuery(default_func=get_7_day_range)
DateRangeParamDep = Annotated[DateRange, Depends(current_date_range_query)]

__all__ = [
    "ActionItemsDep",
    "AuthorizedEngagementBody",
    "AuthorizedEngagementPath",
    "CurrentDateParamDep",
    "DateRangeParamDep",
    "GetUserDep",
    "ManagerBookingsServiceTypesDep",
    "fetch_booking_service_types",
    "fetch_engagement_evidence_uploads",
    "fetch_engagement_links",
]
