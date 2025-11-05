import logging

from fastapi import APIRouter
from sqlalchemy import select, update
from sqlalchemy.sql.functions import func

from api.dependencies import GetSessionDep, GetUserDep
from api.v2.orm import V2BuyingPrograms, booking_contracts_table

router = APIRouter()

logger = logging.getLogger("api")


@router.put("")
def set_pool_manager(
    db_session: GetSessionDep,
    db_user: GetUserDep,
):
    """
    Claim all 'CXEA - Scale' bookings to the current user to become the Pool Manager.
    """

    update_stmt = (
        update(booking_contracts_table)
        .where(
            booking_contracts_table.c.buying_program_type_id
            == (
                select(V2BuyingPrograms.buying_program_type_id)
                .where(V2BuyingPrograms.buying_program_name == "CXEA - Scale")
                .scalar_subquery()
            )
        )
        .where(booking_contracts_table.c.is_deleted == "F")
        .values(
            claimed_and_managed_by=db_user.user_id,
            updated_by=db_user.cisco_cco_id,
            update_dtm=func.now(),
        )
    )

    logger.info("User %s claimed 'CXEA - Scale' bookings.")

    db_session.exec(update_stmt)
    db_session.commit()

    return {"message": f"Claimed 'CXEA - Scale' bookings by {db_user.cisco_cco_id}"}
