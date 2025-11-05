import datetime
from typing import TYPE_CHECKING, Literal, Optional, TypedDict

from sqlalchemy import DateTime, ForeignKey, Integer, Sequence, String
from sqlalchemy.orm import Mapped, mapped_column

from . import V2Base, V2MetadataBase
from .json_varchar import JSONVarchar

if TYPE_CHECKING:
    from ..models import V2TagAction


class V2ThoughtSpotTaggingSummary(V2Base):
    __tablename__ = "dc_tagging_detail"
    thoughtspot_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("dc_tag_thoughtspot.thoughtspot_id"),
        primary_key=True,
        default=None,
    )
    dc_engagement_id: Mapped[str] = mapped_column(String)
    tagset_name: Mapped[str] = mapped_column(String)
    tag_name: Mapped[str] = mapped_column(String)
    canvas_id: Mapped[int] = mapped_column(Integer)
    comment: Mapped[str] = mapped_column(String)
    count_instances: Mapped[int] = mapped_column(Integer)
    create_dtm: Mapped[datetime.datetime] = mapped_column(DateTime)
    user_action: Mapped[str] = mapped_column(String)
    cisco_cco_id: Mapped[str] = mapped_column(String)
    canvas: Mapped[str] = mapped_column(String)


class ThoughtSportInstanceRequestDict(TypedDict):
    thoughtspot_id: int
    dc_engagement_id: int | None
    user_id: int | None
    tag_ids: list[int]
    tagset_ids: list[int]
    comment: str | None
    user_action: "V2TagAction | Literal['set', 'unset'] | None"
    canvas_id: int | None
    count_instances: int | None
    file_location: str | None


class V2ThoughtSpotInstanceRequests(V2MetadataBase):
    __tablename__ = "dc_thoughtspot_instance_requests"

    thoughtspot_id: Mapped[int] = mapped_column(
        Integer,
        Sequence("seq_dc_request"),
        server_default=Sequence("seq_dc_request").next_value(),
        primary_key=True,
    )
    dc_engagement_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("dc_engagement_hdr.dc_engagement_id")
    )
    user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("dc_users.user_id"))
    tag_ids: Mapped[list] = mapped_column(
        JSONVarchar, server_default="[]"
    )  # No mutations tracked here
    tagset_ids: Mapped[list] = mapped_column(
        JSONVarchar, server_default="[]"
    )  # No mutations tracked here
    comment: Mapped[str | None] = mapped_column(String)
    user_action: Mapped[str | None] = mapped_column(String)
    canvas_id: Mapped[int | None] = mapped_column(Integer)
    count_instances: Mapped[int | None] = mapped_column(Integer)
    file_location: Mapped[str | None] = mapped_column(String)

    def dict(self) -> "ThoughtSportInstanceRequestDict":
        return ThoughtSportInstanceRequestDict(
            thoughtspot_id=self.thoughtspot_id,
            dc_engagement_id=self.dc_engagement_id,
            user_id=self.user_id,
            tag_ids=self.tag_ids,
            tagset_ids=self.tagset_ids,
            comment=self.comment,
            user_action=self.user_action,
            canvas_id=self.canvas_id,
            count_instances=self.count_instances,
            file_location=self.file_location,
        )


__all__ = [
    "V2ThoughtSpotInstanceRequests",
    "V2ThoughtSpotTaggingSummary",
]
