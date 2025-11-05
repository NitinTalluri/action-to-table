import json
import logging
from json import JSONDecodeError
from typing import TYPE_CHECKING, Any, Optional, Union

from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR

from ..models.stored_proc import (
    V2DeleteSuperCustomerParams,
    V2ProcedureNames,
    V2StoredProcedureResult,
    V2UpdateSuperCustomerParams,
)

if TYPE_CHECKING:
    from sqlmodel import Session

    from ...models.stored_proc import TagInstancesParams, UntagInstancesParams
    from ..models import (
        V2BookedContractsStoredProcParams,
        V2CreateSuperCustomerParams,
        V2LinkSDPParams,
        V2LinkSDPSubtaskEnablementsParams,
        V2RevenueCXEAStoredProcParams,
        V2RevenueHTECStoredProcParams,
        V2TagInstancesParams,
        V2UntagInstancesParams,
    )
    from ..models.sdp import UserSDPTimeEntrySparse

    TSPParams = Union[
        V2TagInstancesParams,
        V2UntagInstancesParams,
        TagInstancesParams,
        UntagInstancesParams,
        V2RevenueCXEAStoredProcParams,
        V2RevenueHTECStoredProcParams,
        V2BookedContractsStoredProcParams,
        V2LinkSDPParams,
        V2CreateSuperCustomerParams,
        UserSDPTimeEntrySparse,
        None,
    ]

    TV2SPParams = Union[
        V2CreateSuperCustomerParams,
        V2LinkSDPParams,
        V2LinkSDPSubtaskEnablementsParams,
        V2UpdateSuperCustomerParams,
        V2DeleteSuperCustomerParams,
    ]

logger = logging.getLogger("api")


class StoredProcException(Exception):
    """Stored Procedure can Throw Exceptions that we want to catch and handle in the context of the API"""

    def __init__(self, message: str, error_code: Optional[int] = None):
        super().__init__(message, error_code)
        self.message = message
        self.error_code = error_code

    def __str__(self):
        return f"Error: {self.error_code} : {self.message}"

    def __repr__(self):
        return f"{self.__class__.__name__}: [{self.error_code}] : {self.message}"


def coerce_exception(
    e: ProgrammingError,
) -> Union[ProgrammingError, StoredProcException]:
    """Determine if the ProgrammingError is a database exception or a stored procedure exception"""
    # It will include errno
    orig = getattr(e, "orig", None)
    if orig is None:
        return e
    errno = getattr(orig, "errno", 0)
    if errno not in range(-20004, -20000):
        return e
    msg = getattr(orig, "msg", "")
    return StoredProcException(message=msg, error_code=errno)


def make_stored_proc_statement(*extra_params: str, has_params=True) -> text:
    """
    Create a stored procedure statement template with named parameters.
    If extra_params is not provided, the statement will be a simple CALL IDENTIFIER(:proc_name)(:params)
    Otherwise, the statement will be a CALL IDENTIFIER(:proc_name)(:params, ...) where ... are the extra_params
    keyed by their name.

    Parameters
    ----------
    proc_name : str
        The name of the stored procedure

    has_params : bool
        If True, the statement will include a params parameter, otherwise it will not.
        This is to prevent rendering CALL IDENTIFIER(:proc_name)(NULL) when there are no parameters.

    """

    named_params = ", ".join([f":{param}" for param in ["params", *extra_params]])
    param_str = f"({named_params})" if has_params else "()"
    stmt_tmpl = f"CALL IDENTIFIER(:proc_name){param_str}"
    return text(stmt_tmpl)


def parse_stored_proc_result(result: str):
    """
    We attempt to json.loads the result of the stored procedure. If it fails, We warn and return the raw string

    If the stored_proc handles the exception, and we detect 'Error type', or 'SQLERRM' in the result, we raise
    """

    try:
        parsed = json.loads(result)
    except (JSONDecodeError, TypeError):
        logger.warning("Error parsing result result=%r", result)
        return result

    match parsed:
        case {"Error type": str(error_type), "SQLERRM": str(err_msg)}:
            raise StoredProcException(f"{error_type} {err_msg}")
        case _:
            return parsed


def run_stored_procedure(
    params: "TSPParams",
    session: "Session",
    proc_name: str,
    **kwargs: Any,
) -> Any:
    """
    Generic function to run a stored procedure for Tag and Untag. This will open a nested transaction, and will rollback
    the transaction if an exception is raised and commit if no exception is raised.

    Parameters
    ----------
    params : TSPParams
        The parameters for the stored procedure, if any
    session : Session
        The database session
    proc_name : str
        The name of the stored procedure
    kwargs : Any
        If passed these are additional parameters to be passed to the stored procedure

    """
    match params:
        case None:
            stmt = make_stored_proc_statement(has_params=False).bindparams(
                proc_name=proc_name
            )
        case _:
            stmt = make_stored_proc_statement(
                *kwargs.keys(), has_params=True
            ).bindparams(
                proc_name=proc_name,
                params=params.json(by_alias=True, separators=(",", ":")),
                **kwargs,
            )
    with session:
        try:
            result = session.execute(stmt).scalar()
            session.commit()
        except ProgrammingError as e:
            # SP threw unhandled exception
            ec = coerce_exception(e)
            session.rollback()
            raise ec from e
        except Exception as e:
            logger.exception("Generic Exception proc_name=%r", proc_name)
            session.rollback()
            raise e
    try:
        result = json.loads(result)
    except Exception:
        logger.exception(
            "Error parsing return from proc_name=%r result=%r", proc_name, result
        )

    return result


def run_v2_stored_procedure(
    params: "TV2SPParams",
    session: "Session",
    proc_name: V2ProcedureNames,
) -> V2StoredProcedureResult:
    """
    This is the V2 version of the stored procedure runner. It is nearly identical to the original, but it is more strongly
    typed and returns a standard response object.

    Parameters
    ----------
    params : TSPParams
        The parameters for the stored procedure
    session : Session
        The database session
    proc_name : Union[str, V2ProcedureNames]
        The name of the stored procedure
    """
    proc_name = str(proc_name)
    stmt = make_stored_proc_statement().bindparams(
        proc_name=proc_name, params=params.json(by_alias=True)
    )

    with session:
        try:
            result = session.execute(stmt).scalar()
            session.commit()
        except ProgrammingError as e:
            ec = coerce_exception(e)
            session.rollback()
            raise ec from e
        except Exception as e:
            logger.exception("Generic Exception proc_name=%r", proc_name)
            session.rollback()
            raise e
    try:
        return V2StoredProcedureResult.parse_raw(result)
    except Exception as e:
        return V2StoredProcedureResult(
            success=False, message=f"Parsing Error {e}", code=500
        )


def run_put_time_entries_stored_procedure(
    params: "UserSDPTimeEntrySparse",
    session: "Session",
    logged_user: str,
) -> V2StoredProcedureResult:
    proc_name = "put_user_time_entries"

    stmt = make_stored_proc_statement("logged_user").bindparams(
        proc_name=proc_name,
        params=params.json(by_alias=True, separators=(",", ":")),
        logged_user=logged_user,
    )

    try:
        result = session.execute(stmt).scalar()
        session.commit()
    except ProgrammingError as e:
        ec = coerce_exception(e)
        session.rollback()
        logger.exception("Stored Procedure Exception proc_name=%r", proc_name)
        return V2StoredProcedureResult(
            success=False, message=str(ec), code=HTTP_500_INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        logger.exception("Stored Procedure Exception proc_name=%r", proc_name)
        session.rollback()
        return V2StoredProcedureResult(
            success=False, message=str(e), code=HTTP_500_INTERNAL_SERVER_ERROR
        )

    return V2StoredProcedureResult.parse_raw(result)
