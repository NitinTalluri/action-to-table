from typing import TYPE_CHECKING, Union

from sqlalchemy import text

if TYPE_CHECKING:
    from sqlalchemy import TextClause
    from sqlmodel import Session

    from api.v2.models import DbSchema, TDbSchema


def get_schema_from_session(session: "Session") -> "DbSchema":
    """
    Get the schema from a SQLAlchemy session using the engine URL
    """
    from api.v2.models import DbSchema

    engine_url = session.bind.url.database
    if engine_url is None:
        msg = "Database is None in engine URL"
        raise ValueError(msg)
    schema = engine_url.split("/")[-1].upper()
    try:
        db_schema = DbSchema(schema)
        return db_schema
    except ValueError as e:
        msg = f"Invalid schema: {schema}"
        raise ValueError(msg) from e


def query_table_exists(
    table_name: str, db_schema: Union["DbSchema", "TDbSchema"]
) -> "TextClause":
    """
    Check if a table exists in the database using the information_schema.tables table

    Example:
    ```python
    stmt = query_table_exists("CANVAS_4333_THOUGHT_SPOT", "CPS_DSCI_BR")
    exists = session.execute(stmt).scalar_one()
    """
    stmt = text(
        """
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.tables
        WHERE table_name = :table_name_upper AND table_schema = :db_schema
        )
        """
    ).bindparams(
        table_name_upper=table_name.upper(),
        db_schema=str(db_schema).upper(),
    )
    return stmt
