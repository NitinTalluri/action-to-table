import datetime

from snowflake.sqlalchemy import TIMESTAMP_TZ
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from . import V2Base


class V2CoreTableStatus(V2Base):
    __tablename__ = "dc_core_table_update_dates"
    table_name: Mapped[str] = mapped_column(String, primary_key=True, nullable=False)
    last_updated: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP_TZ, nullable=False, comment="The last time this table was updated"
    )
    last_checked: Mapped[datetime.datetime | None] = mapped_column(
        TIMESTAMP_TZ,
        nullable=True,
        comment="The last time this table was checked for updates",
    )
