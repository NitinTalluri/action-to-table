from datetime import datetime
from typing import Optional

from pydantic.v1 import Field, validator

from .. import Model, V2RecordMetaData
from .enums import AnnouncementCategory, AnnouncementPriority


class V2AnnouncementLinkWrite(Model):
    name: str
    href: str


class V2AnnouncementLinkBase(Model):
    """
    Announcement Link base model for creating an Announcement Link
    """

    id: Optional[int]
    name: str
    href: str


class V2AnnouncementLinkBaseRead(Model):
    """
    Announcement Link base model for reading base model of an Announcement Link
    """

    id: int
    name: str
    href: str


class V2AnnouncementLinkRead(V2RecordMetaData):
    """
    Pydantic model for representing a row in the Announcement Link table.
    __tablename__ = "dc_announcement_link"
    """

    id: int
    name: str
    href: str
    announcement_id: int


class V2UserAnnouncementBase(Model):
    """
    User Announcement base model for Create & Update User <-> Announcement relationship
    """

    announcement_id: int
    user_id: str
    is_dismissed: bool


class V2UserAnnouncementRead(V2RecordMetaData):
    """
    Pydantic model for representing a row in the User <-> Announcement table.
    __tablename__ = "dc_user_to_announcement"
    """

    announcement_id: int
    user_id: str
    is_dismissed: bool


class V2AnnouncementBase(Model):
    """
    Announcement Base model for Create & Update an Announcement
    """

    title: str = Field(..., example="My Announcement Title")
    subtitle: Optional[str] = Field(None, example="My Announcement Subtitle")
    body: str = Field(
        ..., example="My Announcement Body. This is the body of the announcement."
    )
    category: AnnouncementCategory = Field(..., example=AnnouncementCategory.General)
    priority: AnnouncementPriority = Field(..., example=AnnouncementPriority.Low)
    push_date: datetime
    expiration_date: datetime
    audience: list[str] = Field(..., example=["manager@cisco.com"])
    links: list[V2AnnouncementLinkWrite] = Field(
        ..., example=[{"name": "Link 1", "href": "https://www.google.com"}]
    )

    @validator("expiration_date")
    def check_expiration_date(cls, v, values):
        if "push_date" in values and v <= values["push_date"]:
            raise ValueError("expiration_date must be after push_date")
        return v


class V2AnnouncementUpdate(Model):
    subtitle: Optional[str]
    body: str
    category: AnnouncementCategory
    priority: AnnouncementPriority
    push_date: datetime
    expiration_date: datetime
    audience: list[str]
    links: list[V2AnnouncementLinkBase]


class V2AnnouncementRead(Model):
    """
    Announcement Read model inherited from V2AnnouncementBase for Read operation for an Announcement
    """

    id: int
    title: str
    subtitle: Optional[str]
    body: str
    category: AnnouncementCategory
    priority: AnnouncementPriority
    push_date: datetime
    expiration_date: datetime
    audience: list[str]
    links: list[V2AnnouncementLinkBaseRead]
    is_dismissed_by_user: bool


class V2AnnouncementStatusBase(Model):
    """
    Announcement Status Update Base model to modify dismissed for a User
    """

    is_dismissed: bool
