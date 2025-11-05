from __future__ import annotations

import datetime
from typing import Optional, Union

from pydantic.v1 import Field

from . import (
    Model,
    V2AcatLinkType,
    V2MceLinkType,
    V2PartyLinkType,
    V2SmartLinkType,
)


class V2AcatLinkBase(Model):
    link_type: V2AcatLinkType = Field("acat_links", exclude=True)


class V2MceLinkBase(Model):
    link_type: V2MceLinkType = Field("mce_links", exclude=True)


class V2PartyLinkBase(Model):
    link_type: V2PartyLinkType = Field("party_links", exclude=True)


class V2SmartLinkBase(Model):
    link_type: V2SmartLinkType = Field("smart_links", exclude=True)


class V2GenericLinkBase(Model):
    __root__: Union[V2AcatLinkBase, V2MceLinkBase, V2PartyLinkBase, V2SmartLinkBase] = (
        Field(discriminator="link_type")
    )


class V2AcatLinkWrite(V2AcatLinkBase):
    id: int
    dc_engagement_id: int


class V2MceLinkWrite(V2MceLinkBase):
    id: int
    dc_engagement_id: int


class V2PartyLinkWrite(V2PartyLinkBase):
    id: int
    dc_engagement_id: int


class V2SmartLinkWrite(V2SmartLinkBase):
    id: int
    dc_engagement_id: int


class V2GenericLinkWrite(Model):
    __root__: Union[
        V2AcatLinkWrite, V2MceLinkWrite, V2PartyLinkWrite, V2SmartLinkWrite
    ] = Field(discriminator="link_type")


class V2AcatLinkUpdate(V2AcatLinkBase):
    dc_engagement_id: int


class V2MceLinkUpdate(V2MceLinkBase):
    dc_engagement_id: int


class V2PartyLinkUpdate(V2PartyLinkBase):
    dc_engagement_id: int


class V2SmartLinkUpdate(V2SmartLinkBase):
    dc_engagement_id: int


class V2GenericLinkUpdate(Model):
    __root__: Union[
        V2AcatLinkUpdate, V2MceLinkUpdate, V2PartyLinkUpdate, V2SmartLinkUpdate
    ] = Field(discriminator="link_type")


class V2AcatLinkRead(V2AcatLinkBase):
    id: int
    dc_engagement_id: int
    link_type: V2AcatLinkType = Field("acat_links", exclude=False)
    last_updated: Optional[datetime.date] = None


class V2MceLinkRead(V2MceLinkBase):
    id: int
    dc_engagement_id: int
    link_type: V2MceLinkType = Field("mce_links", exclude=False)
    last_updated: Optional[datetime.date] = None


class V2PartyLinkRead(V2PartyLinkBase):
    id: int
    dc_engagement_id: int
    link_type: V2PartyLinkType = Field("party_links", exclude=False)
    last_updated: Optional[datetime.date] = None


class V2SmartLinkRead(V2SmartLinkBase):
    id: int
    dc_engagement_id: int
    link_type: V2SmartLinkType = Field("smart_links", exclude=False)
    last_updated: Optional[datetime.date] = None


class V2GenericLinkRead(Model):
    __root__: Union[V2AcatLinkRead, V2MceLinkRead, V2PartyLinkRead, V2SmartLinkRead] = (
        Field(discriminator="link_type")
    )


class V2AcatLinkDelete(V2AcatLinkWrite):
    link_type: V2AcatLinkType = Field("acat_links", exclude=False)


class V2MceLinkDelete(V2MceLinkWrite):
    link_type: V2MceLinkType = Field("mce_links", exclude=False)


class V2PartyLinkDelete(V2PartyLinkWrite):
    link_type: V2PartyLinkType = Field("party_links", exclude=False)


class V2SmartLinkDelete(V2SmartLinkWrite):
    link_type: V2SmartLinkType = Field("smart_links", exclude=False)


class V2GenericLinkDelete(Model):
    __root__: Union[
        V2AcatLinkDelete, V2MceLinkDelete, V2PartyLinkDelete, V2SmartLinkDelete
    ] = Field(discriminator="link_type")


class V2EngagementLinks(Model):
    acat_links: list[V2AcatLinkRead] = Field(default_factory=list)
    mce_links: list[V2MceLinkRead] = Field(default_factory=list)
    party_links: list[V2PartyLinkRead] = Field(default_factory=list)
    smart_links: list[V2SmartLinkRead] = Field(default_factory=list)
