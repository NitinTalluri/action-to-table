from sqlalchemy import Identity, Integer, String, func
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column

from api.v2.orm import V2MetadataBase


class SDPAnchorDateIterator(V2MetadataBase):
    __tablename__ = "dc_sdp_typ_anchor_date_iterator"

    iterator_id: Mapped[int] = mapped_column(
        Integer,
        Identity(start=1, increment=1, order=False),
        nullable=False,
        primary_key=True,
    )
    iterator_date_name: Mapped[str] = mapped_column(
        String(5000), unique=True, nullable=False
    )

    @hybrid_property
    def extra(self):
        return {"is_direct": self.iterator_date_name.lower() == "one-time"}

    @extra.expression
    def extra(cls):
        return func.to_json(
            func.object_construct(
                "is_direct", cls.iterator_date_name.ilike("%one-time%")
            )
        )


class SDPAnchorDate(V2MetadataBase):
    __tablename__ = "dc_sdp_typ_anchor_date"

    anchor_date_id: Mapped[int] = mapped_column(
        Integer,
        Identity(start=1, increment=1, order=False),
        nullable=False,
        primary_key=True,
    )
    anchor_date_name: Mapped[str] = mapped_column(
        String(5000), unique=True, nullable=False
    )


__all__ = [
    "SDPAnchorDate",
    "SDPAnchorDateIterator",
]
