from typing import cast

from sqlalchemy import ForeignKey, Integer, Sequence, String
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, backref, mapped_column, relationship

from .. import V2MetadataBase


class V2ActionItem(V2MetadataBase):
    __tablename__ = "dc_wf_action_item"

    tree_id: Mapped[int] = mapped_column(
        Integer, Sequence("dc_wf_action_item_seq"), primary_key=True
    )
    action_label: Mapped[str] = mapped_column(
        String(1 << 16), nullable=False, unique=True
    )
    ui_enum: Mapped[str | None] = mapped_column(String(1 << 16), nullable=True)

    parent_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("dc_wf_action_item.tree_id"), nullable=True
    )
    children = relationship(
        "V2ActionItem",
        backref=backref("parent", remote_side=[tree_id]),
        uselist=True,
    )

    @hybrid_property
    def child_ids(self) -> list[int]:
        children = cast("list[V2ActionItem]", self.children)
        return [child.tree_id for child in children]
