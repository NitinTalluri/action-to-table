from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, text

if TYPE_CHECKING:
    from sqlalchemy.sql.selectable import TextualSelect


def query_last_updated_dates() -> "TextualSelect":
    from api.v2.orm import V2CoreTableStatus

    stmt = (
        text(
            """
        SELECT table_name,
         MAX(last_updated) AS last_updated
        FROM IDENTIFIER(:table_name)
        GROUP BY table_name
        """
        )
        .bindparams(table_name=V2CoreTableStatus.__tablename__)
        .columns(
            table_name=String,
            last_updated=DateTime,
        )
    )
    return stmt
