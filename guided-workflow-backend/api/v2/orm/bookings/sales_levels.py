from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .. import V2Base


class V2SalesLevel(V2Base):
    __tablename__ = "dc_sales_level"

    sl_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )
    node_level1: Mapped[str] = mapped_column(String, nullable=False)
    node_level2: Mapped[str] = mapped_column(String, nullable=False)
    node_level3: Mapped[str] = mapped_column(String, nullable=False)
    node_level4: Mapped[str] = mapped_column(String, nullable=False)
    node_segment: Mapped[str] = mapped_column(String, nullable=False)


__all__ = [
    "V2SalesLevel",
]
