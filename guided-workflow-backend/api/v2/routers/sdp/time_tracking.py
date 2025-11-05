import logging
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from api.dependencies import (
    CurrentDateParamDep,
    DateRangeParamDep,
    GetSessionDep,
    GetUserDep,
)
from api.v2.models.sdp import (
    UserSDPTimeEntryDetail,
    UserSDPTimeEntrySparse,
    UserSDPWeeklyIndex,
)
from api.v2.queries import (
    get_user_time_tracking_detail,
    get_weekly_summary,
    run_stored_procedure,
)
from api.v2.queries.stored_proc import (
    StoredProcException,
    run_put_time_entries_stored_procedure,
)

router = APIRouter()


logger = logging.getLogger("api")


@router.get("/weekly")
def get_weekly_view(
    date: CurrentDateParamDep,
    session: GetSessionDep,
    db_user: GetUserDep,
    n_weeks: Annotated[
        int,
        Query(
            ge=0,
            description="Number of weeks to look forwards and backwards from the date.",
        ),
    ] = 2,
) -> list[UserSDPWeeklyIndex]:
    """
    Given a date, returns a list of weeks +/- n_weeks from the date. If date is None, defaults to today (UTC Timezone).

    If the date does not fall on a Monday, it will be adjusted to the previous Monday.
    """
    results = get_weekly_summary(
        reference_date=date,
        n_weeks=n_weeks,
        session=session,
        dc_user_id=db_user.user_id,
    )

    return results


@router.get("")
def get_user_time_tracking(
    date_range: DateRangeParamDep,
    session: GetSessionDep,
    db_user: GetUserDep,
) -> UserSDPTimeEntryDetail:
    """
        Retrieves time tracking entries for the current user within the specified date range.

    ### Data Model Complexity

    The returned data represents a complex relationship between deliverables, bookings, engagements and time entries:

    #### Deliverable Hierarchy

    Deliverables are part of the Service Delivery Plan (SDP) and are connected through a hierarchy of sub-tasks and tasks.
    Whether a deliverable is associated with a booking contract or not is determined at the sub-task level.

    #### User-Deliverable Relationship
    Users and deliverables are not directly related. Instead:
    - Sub-tasks are associated with tasks, which are associated with deliverables
    - Booking contracts connect to engagements through users (a three-part key relationship tracked in `DC_ENGAGEMENT_TO_BOOKINGS_RESPONSIBLE_USERS`)

    #### Entry Types
     The response contains a discriminated union of two types of entries:

    **Concrete Deliverables**

    Regular deliverables tied to engagements and booking contracts

    **Abstract Deliverables**

    Special categories like PTO, vacation, or innovation time that are directly associated with a user but are not tracked against a specific deliverable, engagement or booking contract.

    ### UI Considerations

    - The response may contain what appear to be duplicate entries (same deliverable ID, booking contract,
    but different engagement IDs) for a given day.  The data is returned in this format to allow flexibility in the UI for filtering and displaying.
    The UI is free to aggregate and filter the data as needed to present it to the user for viewing/editing.

    | Date       | Deliverable ID | Booking Contract | Engagement ID |
    | ---------- |----------------|------------------|---------------|
    | 2023-01-02 | 6              | ABC              | 5678          |
    | 2023-01-02 | 6              | ABC              | 9012          |
    | 2023-01-02 | 6              | DEF              | 5678          |

    - It is clear that the engagement 5678 is associated with two different booking contracts (ABC and DEF)


    - The UI should display these entries in the most user-friendly way for viewing/editing

    ### Sample UI Representation (All Entries for User)

    In this example, we show one page of time entries for a user, with the following UI representation:

    | Date        | Deliverable ID | Hours |
    |-------------|----------------|-------|
    | 2023-01-02  | 6              | 8     |

    The UI may display the above, but internally, should represent the data as:

    | Date       | Deliverable ID | Booking Contract | Engagement ID | Hours |
    |------------|----------------|------------------|---------------|-------|
    | 2023-01-02 | 6              | ABC              | 5678          | 8/3   |
    | 2023-01-02 | 6              | ABC              | 9012          | 8/3   |
    | 2023-01-02 | 6              | DEF              | 5678          | 8/3   |

    - When submitting time entries back to the API, hours should be distributed evenly across each
    applicable deliverable per day

    ### Sample UI Representation (All Entries for User, Engagement)

    In this example, we show one page of time entries for a user, after filtering by engagement, with the following UI representation:

    | Date        | Deliverable ID | Engagement ID | Hours |
    |-------------|----------------|---------------|-------|
    | 2023-01-02  | 6              | 5678          | 8     |

    - The UI may display the above, but internally, should represent the data as:

    | Date        | Deliverable ID | Booking Contract | Engagement ID | Hours |
    |-------------|----------------|------------------|---------------|-------|
    | 2023-01-02  | 6              | ABC              | 5678          | 8/2   |
    | 2023-01-02  | 6              | DEF              | 5678          | 8/2   |

    ### Sample UI Representation (All Entries for User, Booking Contract)

    In this example, we show one page of time entries for a user, after filtering by booking contract, with the following UI representation:

    | Date        | Deliverable ID | Booking Contract | Hours |
    |-------------|----------------|------------------|-------|
    | 2023-01-02  | 6              | ABC              | 8     |

    - The UI may display the above, but internally, should represent the data as:

    | Date        | Deliverable ID | Booking Contract | Engagement ID | Hours |
    |-------------|----------------|------------------|---------------|-------|
    | 2023-01-02  | 6              | ABC              | 5678          | 8/2   |
    | 2023-01-02  | 6              | ABC              | 9012          | 8/2   |


    """
    result = get_user_time_tracking_detail(
        start_date=date_range.start_date,
        end_date=date_range.end_date,
        dc_user_id=db_user.user_id,
        session=session,
    )
    return result


@router.post("")
def submit_user_time_tracking(
    session: GetSessionDep,
    db_user: GetUserDep,
    payload: UserSDPTimeEntrySparse,
) -> UserSDPTimeEntryDetail:
    """
    Submits time tracking entries for the current user.

    The entries can be a subset of the entries returned by the `get_user_time_tracking` endpoint.
    """

    logged_user = db_user.cisco_cco_id

    result = run_put_time_entries_stored_procedure(
        params=payload, session=session, logged_user=logged_user
    )

    if not result.success:
        raise HTTPException(
            status_code=result.code,
            detail=f"Stored Procedure Error: {result.message}",
        )

    entry_dates = [entry.__root__.entry_date for entry in payload.entries]

    query_result = get_user_time_tracking_detail(
        start_date=min(entry_dates),
        end_date=max(entry_dates),
        dc_user_id=db_user.user_id,
        session=session,
    )
    return query_result
