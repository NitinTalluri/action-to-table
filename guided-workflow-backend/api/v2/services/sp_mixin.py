import logging
from json import JSONDecodeError
from typing import TYPE_CHECKING, Generic, TypeVar

from pydantic.v1 import BaseModel
from sqlalchemy import text

from api.v2.services import ServiceException

if TYPE_CHECKING:
    from sqlalchemy import Engine
    from sqlmodel import Session

logger = logging.getLogger("api")

P = TypeVar("P", bound=BaseModel)


class SPMixin(Generic[P]):
    """Mixin class for calling stored procedures, parsing results and handling errors."""

    def run_stored_procedure(
        self,
        params: P,
        session: "Session",
        proc_name: str,
        **extra_params,
    ):
        from api.v2.queries.stored_proc import make_stored_proc_statement

        stmt = make_stored_proc_statement(*extra_params.keys()).bindparams(
            proc_name=str(proc_name),
            params=params.json(by_alias=True, separators=(",", ":")),
            **extra_params,
        )
        try:
            raw_result = session.execute(stmt).scalar()
        except Exception as e:
            msg = getattr(e, "msg", "")
            logger.exception("Failed to run stored procedure '%s'", proc_name)
            raise ServiceException(f"Failed to run stored procedure {msg}", 500) from e

        from api.v2.queries.stored_proc import StoredProcException

        try:
            from api.v2.queries.stored_proc import parse_stored_proc_result

            parsed = parse_stored_proc_result(raw_result)
            return parsed
        except (JSONDecodeError, TypeError):
            logger.exception(
                "Stored Procedure completed - but could not decode procedure result"
            )
            return None
        except StoredProcException as e:
            logger.exception("Stored Procedure threw exception")
            raise ServiceException(e.message, 500) from e
        except Exception as e:
            logger.exception(
                "Stored Procedure completed - but could not decode procedure result"
            )
            raise ServiceException(
                "Failed to parse stored procedure result", 500
            ) from e


class EngineCompatSPMixin(SPMixin[P]):
    """Mixin class for calling stored procedures, parsing results and handling errors using engine rather than session."""

    def __init__(self, engine: "Engine"):
        self.engine = engine

    def run_stored_procedure(
        self,
        params: P,
        proc_name: str,
        **extra_params,
    ):
        from api.v2.queries.stored_proc import (
            StoredProcException,
            make_stored_proc_statement,
            parse_stored_proc_result,
        )

        stmt = make_stored_proc_statement(*extra_params.keys()).bindparams(
            proc_name=str(proc_name),
            params=params.json(by_alias=True, separators=(",", ":")),
            **extra_params,
        )
        with self.engine.begin() as conn:
            try:
                raw_result = conn.execute(stmt).scalar()
            except Exception as e:
                msg = getattr(e, "msg", "")
                logger.exception("Failed to run stored procedure, '%s'", proc_name)
                raise ServiceException(
                    f"Failed to run stored procedure '{proc_name}', {msg!s}", 500
                ) from e
            try:
                parsed = parse_stored_proc_result(raw_result)
                logger.info("Parsed stored procedure result: %s", parsed)
                if parsed.get("success") is False:
                    logger.error("Stored procedure failed: %s", parsed)
                    raise ServiceException(
                        f"Stored procedure failed: {parsed.get('message')}", 500
                    )
                return parsed
            except (JSONDecodeError, TypeError):
                logger.exception(
                    "Stored Procedure completed - but could not decode procedure result %s",
                    raw_result,
                )
                return None
            except StoredProcException as e:
                logger.exception("Stored Procedure threw exception")
                conn.execute(text("ROLLBACK"))
                raise ServiceException(e.message, 500) from e
            except Exception as e:
                logger.exception(
                    "Stored Procedure completed - but could not decode procedure result %s",
                    raw_result,
                )
                raise ServiceException(
                    "Failed to parse stored procedure result", 500
                ) from e
