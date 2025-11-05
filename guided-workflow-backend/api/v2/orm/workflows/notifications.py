import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Sequence, String, func
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .. import V2MetadataBase
from ..json_varchar import JSONVarchar

if TYPE_CHECKING:
    from api.v2.models import TaskNotificationCreate


class V2Notification(V2MetadataBase):
    __tablename__ = "dc_wf_notification"

    create_dtm: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=func.utc_time(), server_default=func.utc_time()
    )
    update_dtm: Mapped[datetime.datetime | None] = mapped_column(
        DateTime, default=None, onupdate=func.utc_time()
    )
    notification_id: Mapped[int] = mapped_column(
        Integer, Sequence("dc_wf_notification_seq"), primary_key=True
    )
    tree_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("dc_wf_action_item.tree_id"), nullable=False
    )
    dc_engagement_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("dc_engagement_hdr.dc_engagement_id"), nullable=True
    )
    notification_category: Mapped[str] = mapped_column(String(1 << 16), nullable=False)
    subject: Mapped[str] = mapped_column(String(1 << 16), default="")
    data = Column(JSONVarchar)
    dc_user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("dc_users.user_id"), nullable=False
    )

    request_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("dc_wf_background_job.request_id"), nullable=True
    )
    background_job = relationship(
        "V2BackgroundJob",
        uselist=False,
        viewonly=True,
        primaryjoin="and_(V2Notification.request_id == V2BackgroundJob.request_id,"
        " V2BackgroundJob.is_deleted == 'F')",
    )

    def __init__(
        self,
        tree_id: int,
        dc_engagement_id: int,
        notification_category: str,
        data: list[dict],
        dc_user_id: int,
        subject: str = "",
        request_id: Optional[int] = None,
        created_by: Optional[str] = None,
    ):
        self.tree_id = tree_id
        self.dc_engagement_id = dc_engagement_id
        self.notification_category = notification_category
        self.subject = subject
        self.data = data
        self.dc_user_id = dc_user_id
        self.request_id = request_id
        self.created_by = created_by

    @classmethod
    def bulk_create_from_models(
        cls, models: "list[TaskNotificationCreate]", logged_user: str
    ) -> "list[V2Notification]":
        return [
            cls(
                tree_id=model.tree_id,
                dc_engagement_id=model.dc_engagement_id,
                notification_category=model.notification_category,
                subject=model.subject,
                data=[msg.dict() for msg in model.data],
                dc_user_id=model.dc_user_id,
                request_id=model.request_id,
                created_by=logged_user,
            )
            for model in models
        ]

    @hybrid_property
    def last_activity(self) -> datetime.datetime:
        if not self.update_dtm:
            return self.create_dtm
        return max(self.create_dtm, self.update_dtm)

    @last_activity.expression
    def last_activity(cls):
        return func.coalesce(
            func.greatest(cls.create_dtm, cls.update_dtm),
            cls.create_dtm,
            cls.update_dtm,
            func.to_timestamp("2000-01-01 00:00:00"),
        )
