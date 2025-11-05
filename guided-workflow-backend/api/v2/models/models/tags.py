from __future__ import annotations

from typing import Optional

from pydantic.v1 import conint

from . import Model


class V2TagRead(Model):
    tag_id: int
    tag_name: Optional[str]
    tag_desc: Optional[str]
    tagset_id: Optional[int]


class V2TagWrite(Model):
    tag_name: Optional[str]
    tag_desc: Optional[str]
    tagset_id: conint(ge=0)


class V2TagUpdate(Model):
    tag_name: Optional[str] = None
    tag_desc: Optional[str] = None
