from typing import Optional

from sqlalchemy import ForeignKey, Integer, Sequence, String
from sqlalchemy.orm import Mapped, mapped_column

from . import V2MetadataBase


class DocumentationLinks(V2MetadataBase):
    __tablename__ = "dc_documentation_links"

    doc_id: Mapped[int] = mapped_column(
        Integer,
        Sequence("seq_dc_generic"),
        primary_key=True,
        server_default=Sequence("seq_dc_generic").next_value(),
    )
    doc_url: Mapped[str] = mapped_column(String)
    doc_desc: Mapped[str] = mapped_column(String)
    doc_type: Mapped[str] = mapped_column(String)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    ui_enum: Mapped[str] = mapped_column(
        "ui_enum", String(1 << 16), ForeignKey("dc_wf_action_item.ui_enum")
    )

    def __init__(
        self,
        doc_url: Optional[str],
        doc_desc: Optional[str],
        doc_type: Optional[str],
        position: Optional[int],
        ui_enum: Optional[str],
        created_by: str,
    ):
        self.doc_url = doc_url
        self.doc_desc = doc_desc
        self.doc_type = doc_type
        self.position = position
        self.ui_enum = ui_enum
        self.created_by = created_by
        self.is_deleted = "F"
