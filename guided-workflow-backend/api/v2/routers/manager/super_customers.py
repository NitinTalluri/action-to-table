import logging

from fastapi import APIRouter, HTTPException

from api.dependencies import (
    GetSessionDep,
    GetUserDep,
)
from api.v2.models.manager import (
    V2SuperCustomerCreatePayload,
    V2SuperCustomerResponse,
    V2SuperCustomerUpdatePayload,
)
from api.v2.models.stored_proc import (
    V2CreateSuperCustomerParams,
    V2DeleteSuperCustomerParams,
    V2ProcedureNames,
    V2UpdateSuperCustomerParams,
)
from api.v2.queries import (
    get_super_customer_response,
)
from api.v2.queries.stored_proc import run_v2_stored_procedure

logger = logging.getLogger("api")
router = APIRouter()


@router.get("")
def get_super_customers(
    session: GetSessionDep,
) -> V2SuperCustomerResponse:
    """
    Get a multi-purpose response for displaying and managing Super Customers. To keep a response JSON lightweight, we
    avoid the use of arrays of objects.

    The UI can validate that a given dc_engagement_id is available to be associated with a super customer by checking
    the available_dc_engagement_ids list. This is a list of distinct dc_engagement_ids that are not already associated
    with any super customer. The UI can then use the names map to display the name of the engagement.

    ***
    **Response**

    * **names**
      * A Map of `dc_engagement_id` : `engagement_name` of <ins>all</ins> Engagements
      * **Note**: The `dc_engagement_id` is converted to a string for compatibility with JavaScript.
    * **super_customers**
      * Existing super_customers and their associated dc_engagement_ids
    * **available_dc_engagement_ids**
      * A list of distinct dc_engagement_ids that are not already in super_customers

    """
    result = get_super_customer_response(db_session=session)

    return V2SuperCustomerResponse(
        names=result.names,
        super_customers=result.super_customers,
        available_dc_engagement_ids=result.available_engagements,
    )


@router.post("")
def create_super_customer(
    payload: V2SuperCustomerCreatePayload,
    db_user: GetUserDep,
    session: GetSessionDep,
) -> V2SuperCustomerResponse:
    """
    Create a new Super Customer, and optionally associate it with existing engagements.
    """

    sp_params = V2CreateSuperCustomerParams(
        logged_user=db_user.cisco_cco_id,
        super_customer_name=payload.super_customer_name,
        dc_engagement_ids=payload.dc_engagement_ids,
    )
    result = run_v2_stored_procedure(
        params=sp_params,
        session=session,
        proc_name=V2ProcedureNames.create_super_customer,
    )

    if not result.success:
        logger.error(
            "Failed to create super customer: %s %s", result.message, result.logs
        )
        session.rollback()
        raise HTTPException(
            status_code=result.code,
            detail=result.message,
        )
    logger.info(
        "Super customer created successfully: %s %s", result.message, result.logs
    )
    session.commit()

    # If successful, get the updated super customer response
    response = get_super_customer_response(db_session=session)

    # Return the response
    return V2SuperCustomerResponse(
        names=response.names,
        super_customers=response.super_customers,
        available_dc_engagement_ids=response.available_engagements,
    )


@router.put("/{super_customer_id}")
def update_super_customer(
    super_customer_id: int,
    payload: V2SuperCustomerUpdatePayload,
    db_user: GetUserDep,
    session: GetSessionDep,
) -> V2SuperCustomerResponse:
    """
    Modify an existing Super Customer, including renaming it, and setting its associated engagements to the provided list.
    Pre-existing engagements will be dropped.
    """

    if super_customer_id != payload.super_customer_id:
        raise HTTPException(
            status_code=400,
            detail="Super customer ID in URL does not match ID in payload",
        )

    sp_params = V2UpdateSuperCustomerParams(
        logged_user=db_user.cisco_cco_id,
        super_customer_id=payload.super_customer_id,
        super_customer_name=payload.super_customer_name,
        dc_engagement_ids=payload.dc_engagement_ids,
    )

    result = run_v2_stored_procedure(
        params=sp_params,
        session=session,
        proc_name=V2ProcedureNames.update_super_customer,
    )

    if not result.success:
        logger.error(
            "Failed to update super customer: %s %s", result.message, result.logs
        )
        session.rollback()
        raise HTTPException(
            status_code=result.code,
            detail=result.message,
        )

    logger.info(
        "Super customer updated successfully: %s %s", result.message, result.logs
    )

    session.commit()
    # If successful, get the updated super customer response
    response = get_super_customer_response(db_session=session)
    # Return the response
    return V2SuperCustomerResponse(
        names=response.names,
        super_customers=response.super_customers,
        available_dc_engagement_ids=response.available_engagements,
    )


@router.delete("/{super_customer_id}")
def delete_super_customer(
    super_customer_id: int,
    db_user: GetUserDep,
    session: GetSessionDep,
) -> V2SuperCustomerResponse:
    """
    Soft delete a super customer and mark it's associated engagements as available.
    """

    sp_params = V2DeleteSuperCustomerParams(
        logged_user=db_user.cisco_cco_id,
        super_customer_id=super_customer_id,
    )

    result = run_v2_stored_procedure(
        params=sp_params,
        session=session,
        proc_name=V2ProcedureNames.delete_super_customer,
    )

    if not result.success:
        logger.error(
            "Failed to delete super customer: %s %s", result.message, result.logs
        )
        session.rollback()
        raise HTTPException(
            status_code=result.code,
            detail=result.message,
        )

    logger.info(
        "Super customer deleted successfully: %s %s", result.message, result.logs
    )
    session.commit()

    # If successful, get the updated super customer response
    response = get_super_customer_response(db_session=session)
    # Return the response
    return V2SuperCustomerResponse(
        names=response.names,
        super_customers=response.super_customers,
        available_dc_engagement_ids=response.available_engagements,
    )
