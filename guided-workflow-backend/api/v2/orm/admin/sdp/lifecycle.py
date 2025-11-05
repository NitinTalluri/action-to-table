from sqlalchemy import Integer, Sequence, String
from sqlalchemy.orm import Mapped, mapped_column

from api.v2.orm import V2MetadataBase


class SDPLifeCycle(V2MetadataBase):
    __tablename__ = "dc_sdp_typ_lifecycle"

    lifecycle_id: Mapped[int] = mapped_column(
        Integer, Sequence("seq_dc_sdp"), primary_key=True
    )
    lifecycle_desc: Mapped[str] = mapped_column(
        String(5000), default="", unique=True, nullable=False
    )
    lifecycle_doc_link: Mapped[str] = mapped_column(
        String(5000), default="", nullable=False, server_default=""
    )
