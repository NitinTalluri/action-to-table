import datetime
from typing import TYPE_CHECKING

from dateutil.relativedelta import MO, SU, relativedelta
from sqlalchemy import Boolean, Date, Float, Integer, String, text

from api.v2.models import safe_parse_collection
from api.v2.models.sdp import UserSDPTimeEntryDetail, UserSDPWeeklyIndex

if TYPE_CHECKING:
    from sqlalchemy.sql.selectable import TextualSelect
    from sqlmodel import Session


def query_user_time_tracking_detail(
    dc_user_id: int,
    start_date: datetime.date,
    end_date: datetime.date,
) -> "TextualSelect":
    """
    Generate a SQL query that:
    - Uses a recursive CTE to generate the date range between start_date and end_date.
    - Joins to another CTE (ASSIGNED_DELIVERABLES) that determines what deliverables were relevant and assigned to the user during that time.
        If the deliverable_id is active for at least one day in the date range, it is included.
    - Joins to dc_sdp_abstract_deliverable for
    - Joins to the time tracking table to get the total time spent on each deliverable_id,engagement,booking per day. If no time tracking exists for a given deliverable_id, we use NVL, to return 0.
    """

    stmt = (
        text(
            """WITH
    RECURSIVE
    DAYS                  AS (SELECT CAST(:start_date AS DATE) AS DAY
                              UNION ALL
                              SELECT DATEADD( 'DAY', 1, DAY )
                                  FROM
                                      DAYS
                                  WHERE
                                      DAY < CAST(:end_date AS DATE)
                             ),
    ASSIGNED_DELIVERABLES AS (SELECT
                                  DELIVERABLE_ID,
                                  NULL AS ABSTRACT_DELIVERABLE_ID,
                                  DELIVERABLE_DESC,
                                  MIN_OPEN_DATE,
                                  MAX_OPEN_DATE,
                                  DL.DC_ENGAGEMENT_ID,
                                  DL.BOOKING_CONTRACT,
                                  USR.USER_ID AS DC_USER_ID,
                                  FALSE AS IS_ABSTRACT
                                  FROM
                                      DC_DELIVERABLES_OWED_SCHEDULED_ENG DL
                                          JOIN DC_ENGAGEMENT_TO_BOOKINGS_RESPONSIBLE_USER ERU
                                               ON (DL.BOOKING_CONTRACT = ERU.BOOKING_CONTRACT AND
                                                   DL.DC_ENGAGEMENT_ID = ERU.DC_ENGAGEMENT_ID AND
                                                   ERU.IS_DELETED = 'F' AND ERU.DC_USER_ID = :dc_user_id)
                                                   
                                          JOIN DC_USERS USR
                                                ON (USR.USER_ID = ERU.DC_USER_ID AND
                                                    USR.IS_DELETED = 'F')
                                                    
                                    WHERE
                                    CAST(:start_date AS DATE) BETWEEN MIN_OPEN_DATE AND MAX_OPEN_DATE
                                    OR
                                    CAST(:end_date AS DATE) BETWEEN MIN_OPEN_DATE AND MAX_OPEN_DATE
    ),
    ABSTRACT_DELIVERABLES AS (
                        SELECT ABSTRACT_DELIVERABLE_ID,
                               NULL AS DELIVERABLE_ID,
                               ABSTRACT_DELIVERABLE_DESC AS DELIVERABLE_DESC,
                               NULL AS MIN_OPEN_DATE,
                               NULL AS MAX_OPEN_DATE,
                               NULL AS DC_ENGAGEMENT_ID,
                               NULL AS BOOKING_CONTRACT,
                               :dc_user_id AS DC_USER_ID,
                               TRUE AS IS_ABSTRACT
                               FROM DC_SDP_TYP_ABSTRACT_DELIVERABLE
                               WHERE IS_DELETED = 'F'
    ),
    ALL_DELIVERABLES AS (SELECT
                            DELIVERABLE_ID,
                            ABSTRACT_DELIVERABLE_ID,
                            DELIVERABLE_DESC,
                            MIN_OPEN_DATE,
                            MAX_OPEN_DATE,
                            DC_ENGAGEMENT_ID,
                            BOOKING_CONTRACT,
                            DC_USER_ID,
                            IS_ABSTRACT
                            FROM ASSIGNED_DELIVERABLES
                            UNION ALL
                            SELECT
                                DELIVERABLE_ID,
                                ABSTRACT_DELIVERABLE_ID,
                                DELIVERABLE_DESC,
                                MIN_OPEN_DATE,
                                MAX_OPEN_DATE,
                                DC_ENGAGEMENT_ID,
                                BOOKING_CONTRACT,
                                DC_USER_ID,
                                IS_ABSTRACT
                            FROM ABSTRACT_DELIVERABLES
                            ),
    DAILY_ENTRIES AS (SELECT DISTINCT
                          DAYS.DAY AS ENTRY_DATE,
                          AD.DELIVERABLE_ID,
                          AD.ABSTRACT_DELIVERABLE_ID,
                          AD.DELIVERABLE_DESC,
                          AD.BOOKING_CONTRACT,
                          AD.DC_ENGAGEMENT_ID,
                          AD.DC_USER_ID,
                          AD.IS_ABSTRACT,
                          DD.FISCAL_YEAR_NUMBER,
                          DD.FISCAL_QUATER_NUMBER AS QUARTER,
                          WEEKISO(DAYS.DAY) AS WEEK_NUM_IN_YEAR,
                          DD.YEAR
                          FROM
                              DAYS
                                  LEFT JOIN ALL_DELIVERABLES AD
                                  
                                  JOIN      CPS_DSCI_ARCHIVE.DIM_DATE_NEW DD
                                            ON (DAYS.DAY = DD.DATE)

                          ORDER BY
                              DAYS.DAY,
                              AD.DELIVERABLE_DESC,
                              AD.BOOKING_CONTRACT,
                              AD.DC_ENGAGEMENT_ID
                     ),
    DAILY_HOURS AS (
        SELECT DAILY.ENTRY_DATE,
               DAILY.DELIVERABLE_ID,
               DAILY.ABSTRACT_DELIVERABLE_ID,
               DAILY.DC_ENGAGEMENT_ID,
               DAILY.DC_USER_ID,
               DAILY.DELIVERABLE_DESC,
               DAILY.BOOKING_CONTRACT,
               DAILY.FISCAL_YEAR_NUMBER,
               DAILY.QUARTER,
               DAILY.WEEK_NUM_IN_YEAR,
               DAILY.IS_ABSTRACT,
               NVL(ENTRY.HOURS, 0.0) AS HOURS,
               ENTRY.ENTRY_ID AS ENTRY_ID
        FROM DAILY_ENTRIES DAILY
        LEFT JOIN DC_SDP_TIME_ENTRY ENTRY ON (
            CASE
                WHEN DAILY.IS_ABSTRACT
                 THEN DAILY.ENTRY_DATE = ENTRY.DATE AND
                 DAILY.DC_USER_ID = ENTRY.DC_USER_ID AND
                 DAILY.ABSTRACT_DELIVERABLE_ID = ENTRY.ABSTRACT_DELIVERABLE_ID AND
                 ENTRY.IS_DELETED = 'F'
                ELSE DAILY.ENTRY_DATE = ENTRY.DATE AND
                DAILY.BOOKING_CONTRACT = ENTRY.BOOKING_CONTRACT AND
                DAILY.DC_ENGAGEMENT_ID = ENTRY.DC_ENGAGEMENT_ID AND
                DAILY.DC_USER_ID = ENTRY.DC_USER_ID AND
                DAILY.DELIVERABLE_ID = ENTRY.DELIVERABLE_ID AND
                ENTRY.IS_DELETED = 'F'
            END

            )
    )
    SELECT
        DH.BOOKING_CONTRACT,
        DH.DC_ENGAGEMENT_ID,
        HDR.ENGAGEMENT_NAME,
        DH.DC_USER_ID,
        DH.DELIVERABLE_DESC,
        DH.DELIVERABLE_ID,
        DH.ABSTRACT_DELIVERABLE_ID,
        DH.ENTRY_ID,
        DH.ENTRY_DATE,
        DH.FISCAL_YEAR_NUMBER,
        DH.HOURS,
        DH.IS_ABSTRACT,
        DH.QUARTER,
        DH.WEEK_NUM_IN_YEAR
    FROM DAILY_HOURS DH
    LEFT JOIN DC_ENGAGEMENT_HDR HDR ON (DH.DC_ENGAGEMENT_ID = HDR.DC_ENGAGEMENT_ID)
"""
        )
        .bindparams(
            start_date=start_date,
            end_date=end_date,
            dc_user_id=dc_user_id,
        )
        .columns(
            booking_contract=Integer,
            dc_engagement_id=Integer,
            engagement_name=String,
            dc_user_id=Integer,
            deliverable_desc=String,
            abstract_deliverable_id=Integer,
            deliverable_id=Integer,
            entry_id=Integer,
            entry_date=Date,
            fiscal_year_number=Integer,
            hours=Float,
            is_abstract=Boolean,
            quarter=Integer,
            week_num_in_year=Integer,
        )
    )

    return stmt


def get_user_time_tracking_detail(
    start_date: datetime.date,
    end_date: datetime.date,
    dc_user_id: int,
    session: "Session",
) -> UserSDPTimeEntryDetail:
    """
    Get user time tracking detail for a given date range.
    """

    query = query_user_time_tracking_detail(
        start_date=start_date,
        end_date=end_date,
        dc_user_id=dc_user_id,
    )

    result = session.execute(query).mappings().all()

    return UserSDPTimeEntryDetail.parse_obj({"entries": result or []})


def query_weekly_summary(
    dc_user_id: int, start_date: datetime.date, end_date: datetime.date
) -> "TextualSelect":
    stmt = (
        text(
            """
       WITH DAYS_CTE AS (
        SELECT
            DATE,
            WEEKISO(DATE ) AS WEEK_NUM_IN_YEAR,
            EXTRACT( YEAR FROM DATE ) AS YEAR,
            FISCAL_YEAR_NUMBER,
            FISCAL_QUATER_NUMBER as QUARTER
        FROM CPS_DSCI_ARCHIVE.DIM_DATE_NEW
        WHERE DATE BETWEEN :start_date AND :end_date
       ), WEEKLY_SUMMARY AS (
         SELECT
            MIN(DATE) AS START_DATE,
            MAX(DATE) AS END_DATE,
            MIN(WEEK_NUM_IN_YEAR) AS WEEK_NUM_IN_YEAR,
            MIN(YEAR) AS YEAR,
            MIN(QUARTER) AS QUARTER,
            MIN(FISCAL_YEAR_NUMBER) AS FISCAL_YEAR_NUMBER
        FROM DAYS_CTE
        GROUP BY YEAR, WEEK_NUM_IN_YEAR
        ORDER BY START_DATE
        ),
        USER_ENTRIES AS (
            SELECT
            DATE,
            HOURS
            FROM DC_SDP_TIME_ENTRY
            WHERE DC_USER_ID = :dc_user_id
            AND DATE BETWEEN :start_date AND :end_date
            AND IS_DELETED = 'F'
            AND HOURS > 0
        ),
        WEEKLY_SUMMARY_WITH_HOURS AS (
            SELECT START_DATE,
                    END_DATE,
                    WEEK_NUM_IN_YEAR,
                    YEAR,
                    QUARTER,
                    FISCAL_YEAR_NUMBER,
                    NVL(SUM(HOURS), 0) AS TOTAL_HOURS
            FROM WEEKLY_SUMMARY
            LEFT JOIN USER_ENTRIES ENTRY ON (
                ENTRY.DATE BETWEEN START_DATE AND END_DATE
            )
            GROUP BY START_DATE, END_DATE, WEEK_NUM_IN_YEAR, YEAR, QUARTER, FISCAL_YEAR_NUMBER
        )
        SELECT
            START_DATE,
            END_DATE,
            WEEK_NUM_IN_YEAR,
            YEAR,
            QUARTER,
            FISCAL_YEAR_NUMBER,
            TOTAL_HOURS
        FROM WEEKLY_SUMMARY_WITH_HOURS
    """
        )
        .bindparams(
            dc_user_id=dc_user_id,
            start_date=start_date,
            end_date=end_date,
        )
        .columns(
            start_date=Date,
            end_date=Date,
            week_num_in_year=Integer,
            year=Integer,
            quarter=Integer,
            fiscal_year_number=Integer,
            total_hours=Float,
        )
    )
    return stmt


def _get_weekly_date_range(
    reference_date: datetime.date,
    n_weeks: int,
) -> tuple[datetime.date, datetime.date]:
    """
    Given a reference date, normalize it to the previous Monday.
    Then calculate the start and end dates for the given number of weeks so that
    the start date is a Monday and the end date is a Sunday.

    Note that the end date is not inclusive.
    """

    rd_monday = relativedelta(weekday=MO(-1))
    rd_end_date = relativedelta(weeks=n_weeks + 1, weekday=SU(-1))
    rd_start_date = relativedelta(weeks=-n_weeks)

    current_date = reference_date + rd_monday
    start_date = current_date + rd_start_date
    end_date = current_date + rd_end_date

    return start_date, end_date


def get_weekly_summary(
    reference_date: datetime.date, n_weeks: int, session: "Session", dc_user_id: int
) -> list[UserSDPWeeklyIndex]:
    """
    Get a high-level summary of each week using reference_date and n_weeks.

    If reference_date does not fall on Monday, it will be adjusted to the previous Monday.
    If it does fall on Monday, no adjustment is made.

    Using n_weeks, we determine the start and end dates for the query. The end_date is not inclusive.
    """

    start_date, end_date = _get_weekly_date_range(
        reference_date=reference_date, n_weeks=n_weeks
    )
    query = query_weekly_summary(
        dc_user_id=dc_user_id, start_date=start_date, end_date=end_date
    )

    results = session.execute(query).mappings().all()

    return safe_parse_collection(list[UserSDPWeeklyIndex], results)
