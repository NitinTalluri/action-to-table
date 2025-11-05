from typing import TYPE_CHECKING, Union

from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import V2MetadataBase

if TYPE_CHECKING:
    from ..models import (
        V2AcatLinkUpdate,
        V2AcatLinkWrite,
        V2MceLinkWrite,
        V2PartyLinkWrite,
        V2SmartLinkWrite,
    )


class V2AcatLink(V2MetadataBase):
    __tablename__ = "dc_acat_links"
    id: Mapped[int] = mapped_column(
        "acat_customer_id", Integer, default=None, primary_key=True
    )
    dc_engagement_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("dc_engagement_hdr.dc_engagement_id"), primary_key=True
    )
    engagement = relationship("V2Engagement", back_populates="acat_links")

    @classmethod
    def create_from_model(cls, model: "V2AcatLinkWrite", logged_user: str, session):
        return super().create_from_model(model, logged_user, session)

    def update_from_model(
        self,
        model: Union["V2AcatLinkWrite", "V2AcatLinkUpdate"],
        logged_user: str,
        session,
    ):
        return super().update_from_model(model, logged_user, session)

    def soft_delete(self, logged_user: str, session):
        return super().soft_delete(logged_user, session)


class V2MceLink(V2MetadataBase):
    __tablename__ = "dc_mce_links"
    id: Mapped[int] = mapped_column(
        "mce_engagement_number", Integer, default=None, primary_key=True
    )
    dc_engagement_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("dc_engagement_hdr.dc_engagement_id"), primary_key=True
    )
    engagement = relationship("V2Engagement", back_populates="mce_links")

    @classmethod
    def create_from_model(cls, model: "V2MceLinkWrite", logged_user: str, session):
        return super().create_from_model(model, logged_user, session)

    def update_from_model(self, model: "V2MceLinkWrite", logged_user: str, session):
        return super().update_from_model(model, logged_user, session)

    def soft_delete(self, logged_user: str, session):
        return super().soft_delete(logged_user, session)


class V2PartyLink(V2MetadataBase):
    __tablename__ = "dc_party_links"
    id: Mapped[int] = mapped_column(
        "cr_party_id", Integer, default=None, primary_key=True
    )
    dc_engagement_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("dc_engagement_hdr.dc_engagement_id"), primary_key=True
    )
    engagement = relationship("V2Engagement", back_populates="party_links")

    @classmethod
    def create_from_model(cls, model: "V2PartyLinkWrite", logged_user: str, session):
        return super().create_from_model(model, logged_user, session)

    def update_from_model(self, model: "V2PartyLinkWrite", logged_user: str, session):
        return super().update_from_model(model, logged_user, session)

    def soft_delete(self, logged_user: str, session):
        return super().soft_delete(logged_user, session)


class V2SmartLink(V2MetadataBase):
    __tablename__ = "dc_smart_account_links"
    id: Mapped[int] = mapped_column(
        "smart_account", Integer, default=None, primary_key=True
    )
    dc_engagement_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("dc_engagement_hdr.dc_engagement_id"), primary_key=True
    )
    engagement = relationship("V2Engagement", back_populates="smart_links")

    @classmethod
    def create_from_model(cls, model: "V2SmartLinkWrite", logged_user: str, session):
        return super().create_from_model(model, logged_user, session)

    def update_from_model(self, model: "V2SmartLinkWrite", logged_user: str, session):
        return super().update_from_model(model, logged_user, session)

    def soft_delete(self, logged_user: str, session):
        return super().soft_delete(logged_user, session)
