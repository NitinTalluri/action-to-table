from datetime import datetime
from typing import Optional

from pydantic.v1 import Field, root_validator, validator

from .. import coerce_notification_data
from ..base import isoformat_utc
from . import (
    CreateMessage,
    Message,
    Model,
    NotificationCategory,
)


class TaskNotificationCreate(Model):
    tree_id: int = Field(
        ..., description="The ID of the tree item this notification is associated with."
    )
    notification_category: NotificationCategory = Field(
        NotificationCategory.PENDING, description="The category of the notification."
    )
    subject: str = Field(
        "",
        description="The subject of the notification. Defaults to an empty string if "
        "not provided",
    )

    dc_user_id: int = Field(
        ..., description="The ID of the user this notification is for."
    )
    dc_engagement_id: Optional[int] = Field(
        ..., description="The Engagement Id this notification is for."
    )
    request_id: Optional[int] = Field(
        None,
        description="Associate a BackgroundJob using request_id with this notification.",
    )
    workflow_enum: Optional[str] = Field(
        None, description="The workflow enum associated with the notification."
    )
    external_job_id: Optional[str] = Field(
        None, description="The external job ID associated with the notification."
    )
    external_run_id: Optional[str] = Field(
        None, description="The external run ID associated with the notification."
    )
    data: list[CreateMessage] = Field(
        default_factory=list, description="Data related to the notification"
    )


class TaskNotificationUpdate(Model):
    notification_category: Optional[NotificationCategory] = Field(
        None, description="The category of the notification."
    )
    subject: Optional[str] = Field(None, description="The subject of the notification")
    data: Optional[list[CreateMessage]] = Field(
        None, description="Additional messages to append to the notification."
    )

    _coerce_notification_data = validator("data", allow_reuse=True, pre=True)(
        coerce_notification_data
    )

    @root_validator(pre=True)
    def coerce_legacy_notification_data(cls, values):
        data_type = values.get("type")
        if not data_type:
            return values
        data = values.get("data")
        match data:
            case {"excel_location": str(url)}:
                values["data"] = [
                    {
                        "type": "download",
                        "data": {"label": "Download Results", "url": url},
                    }
                ]
                return values
        return values


class TaskNotification(Model):
    notification_id: int = Field(..., description="The ID of the notification.")
    tree_id: int = Field(
        ..., description="The ID of the tree item this notification is associated with."
    )
    notification_category: NotificationCategory = Field(
        NotificationCategory.PENDING, description="The category of the notification."
    )
    subject: str = Field(
        "",
        description="The subject of the notification. Defaults to an empty string if "
        "not provided",
    )

    dc_user_id: int = Field(
        ..., description="The ID of the user this notification is for."
    )
    dc_engagement_id: Optional[int] = Field(
        ..., description="The Engagement Id this notification is for."
    )
    request_id: Optional[int] = Field(
        None,
        description="Associate a BackgroundJob using request_id with this notification.",
    )
    canvas_id: Optional[int] = Field(
        None,
        description="The ID of the canvas associated with the notification via BackgroundJob.",
    )
    workflow_enum: Optional[str] = Field(
        None, description="The workflow enum associated with the notification."
    )
    external_job_id: Optional[str] = Field(
        None, description="The external job ID associated with the notification."
    )
    external_run_id: Optional[str] = Field(
        None, description="The external run ID associated with the notification."
    )
    create_dtm: Optional[datetime] = Field(
        ..., description="The date and time the notification was created."
    )
    update_dtm: Optional[datetime] = Field(
        ..., description="The date and time the notification was last updated."
    )
    created_by: Optional[str] = Field(
        ..., description="The cisco_cco_id user who created the notification."
    )


class TaskNotificationDetail(TaskNotification):
    data: list[Message] = Field(
        default_factory=list,
        description="Data related to the notification",
    )

    _coerce_notification_data = validator("data", allow_reuse=True, pre=True)(
        coerce_notification_data
    )

    class Config:
        json_encoders = {datetime: isoformat_utc}
