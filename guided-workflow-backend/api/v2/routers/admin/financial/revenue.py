import logging
from typing import TYPE_CHECKING

from fastapi import APIRouter, BackgroundTasks, HTTPException
from sqlalchemy import text
from starlette.status import HTTP_200_OK, HTTP_202_ACCEPTED

from api.dependencies import GetSessionDep, GetUserDep
from api.v2.models import (
    RevenueType,
    V2RevenueCOGSEntry,
    V2RevenueCOGSStoredProcParams,
    V2RevenueCXEAEntry,
    V2RevenueCXEAStoredProcParams,
    V2RevenueHTECEntry,
    V2RevenueHTECStoredProcParams,
)
from api.v2.models.admin import V2RevenueSEAEntry
from api.v2.models.admin.financial.revenue import V2RevenueSEAStoredProcParams
from api.v2.queries import run_stored_procedure

if TYPE_CHECKING:
    from sqlmodel import Session

logger = logging.getLogger("api")

router = APIRouter()


def run_htec_background(payload: list[V2RevenueHTECEntry], logged_user: str, session):
    logger.info("Running HTEC Import %d entries, user: %s", len(payload), logged_user)
    params = V2RevenueHTECStoredProcParams.construct(
        __root__=payload,
    )
    with session:
        for i, batched_params in enumerate(params.batchify(), start=1):
            logger.info("Running batch #%d", i)
            try:
                run_stored_procedure(
                    params=batched_params,
                    session=session,
                    proc_name="import_htec_revenue_2",
                    logged_user=logged_user,
                )
                logger.info("Finished batch #%d", i)
            except Exception as e:
                logger.exception("Error running HTEC stored procedure")
                session.rollback()
                raise e
        session.commit()

    logger.info("Finished HTEC Import %d entries, user: %s", len(payload), logged_user)


def run_cxea_background(payload: list[V2RevenueCXEAEntry], logged_user: str, session):
    logger.info("Running CXEA Import %d entries, user: %s", len(payload), logged_user)
    params = V2RevenueCXEAStoredProcParams(
        __root__=payload,
    )
    with session:
        for i, batched_params in enumerate(params.batchify(), start=1):
            logger.info("Running batch #%d", i)
            try:
                run_stored_procedure(
                    params=batched_params,
                    session=session,
                    proc_name="import_cxea_revenue_2",
                    logged_user=logged_user,
                )
            except Exception as e:
                logger.exception("Error running CXEA stored procedure")
                session.rollback()
                raise e
        session.commit()

    logger.info("Finished CXEA Import %d entries, user: %s", len(payload), logged_user)


def run_cogs_background(payload: list[V2RevenueCOGSEntry], logged_user: str, session):
    logger.info("Running COGS Import %d entries, user: %s", len(payload), logged_user)
    params = V2RevenueCOGSStoredProcParams(
        __root__=payload,
    )
    with session:
        for i, batched_params in enumerate(params.batchify(), start=1):
            logger.info("Running batch #%d", i)
            try:
                run_stored_procedure(
                    params=batched_params,
                    session=session,
                    proc_name="import_cogs_2",
                    logged_user=logged_user,
                )
            except Exception as e:
                logger.exception("Error running COGS stored procedure")
                session.rollback()
                raise e
        session.commit()

    logger.info("Finished COGS Import %d entries, user: %s", len(payload), logged_user)


def run_sea_background(payload: list[V2RevenueSEAEntry], logged_user: str, session):
    logger.info("Running SEA Import %d entries", len(payload))
    params = V2RevenueSEAStoredProcParams(
        __root__=payload,
    )
    with session:
        for i, batched_params in enumerate(params.batchify(), start=1):
            logger.info("Running batch #%d", i)
            try:
                run_stored_procedure(
                    params=batched_params,
                    session=session,
                    proc_name="import_sea_entries",
                    logged_user=logged_user,
                )
            except Exception as e:
                logger.exception("Error running SEA stored procedure")
                session.rollback()
                raise e
        session.commit()

    logger.info("Finished SEA Import %d entries", len(payload))


def run_table_truncate(session: "Session", revenue_type: RevenueType):
    match revenue_type:
        case RevenueType.CXEA | "cxea":
            table_name = "dc_revenue_cxea"
        case RevenueType.HTEC | "htec":
            table_name = "dc_revenue_htec"
        case RevenueType.COGS | "cogs":
            table_name = "dc_revenue_cogs"
        case _:
            raise HTTPException(status_code=400, detail="Invalid revenue type")

    logger.warning("Truncating revenue table %s", revenue_type)
    stmt = text(f"TRUNCATE TABLE {table_name}")
    session.execute(stmt)
    session.commit()


@router.post("/sea")
def create_sea_revenue_entries(
    payload: list[V2RevenueSEAEntry],
    db_user: GetUserDep,
    background_tasks: BackgroundTasks,
    session: GetSessionDep,
):
    """
    Bulk import SEA revenue entries
    """

    background_tasks.add_task(
        run_sea_background,
        payload=payload,
        session=session,
        logged_user=db_user.cisco_cco_id,
    )
    return {"message": "SEA Import started in the background"}, 202


@router.post("/cxea", status_code=HTTP_202_ACCEPTED)
def create_cxea_revenue_entries(
    data: list[V2RevenueCXEAEntry],
    db_user: GetUserDep,
    background_tasks: BackgroundTasks,
    session: GetSessionDep,
):
    """
    Create revenue entries for cxea
    """
    logged_user = db_user.cisco_cco_id
    background_tasks.add_task(
        run_cxea_background, payload=data, logged_user=logged_user, session=session
    )
    return {"message": "CXEA Import started in the background"}, 202


@router.post("/htec", status_code=HTTP_202_ACCEPTED)
def create_htec_revenue_entries(
    data: list[V2RevenueHTECEntry],
    db_user: GetUserDep,
    background_tasks: BackgroundTasks,
    session: GetSessionDep,
):
    """
    Create revenue entries for HTEC
    """
    logged_user = db_user.cisco_cco_id

    background_tasks.add_task(
        run_htec_background, payload=data, logged_user=logged_user, session=session
    )
    return {"message": "HTEC Import started in the background"}, 202


@router.post("/cogs", status_code=HTTP_202_ACCEPTED)
def create_cogs_revenue_entries(
    data: list[V2RevenueCOGSEntry],
    db_user: GetUserDep,
    background_tasks: BackgroundTasks,
    session: GetSessionDep,
):
    logged_user = db_user.cisco_cco_id
    background_tasks.add_task(
        run_cogs_background, payload=data, logged_user=logged_user, session=session
    )
    return {"message": "COGS Import started in the background"}, 202


@router.post("/clear/{revenue_type}", status_code=HTTP_200_OK)
def truncate_revenue_table(
    revenue_type: RevenueType,
    db_user: GetUserDep,
    session: GetSessionDep,
):
    logger.warning(
        "User %s requested to truncate revenue table %s",
        db_user.cisco_cco_id,
        revenue_type,
    )
    run_table_truncate(session, revenue_type)
    return {"message": f"Cleared '{revenue_type!s}' data"}, 200


@router.post("/process", status_code=HTTP_200_OK)
def process_revenue_tables(
    db_user: GetUserDep,
    session: GetSessionDep,
):
    logger.info("User %s requested to process revenue tables", db_user.cisco_cco_id)
    run_stored_procedure(
        params=None,
        session=session,
        proc_name="process_revenue",
        logged_user=db_user.cisco_cco_id,
    )
    return {"message": "Revenue tables processed"}, 200
