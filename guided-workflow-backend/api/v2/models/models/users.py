from typing import Optional

from pydantic.v1 import Field

from . import Model


class V2UserModel(Model):
    cisco_cco_id: str = Field(..., title="Cisco CCO ID", example="auser123@cisco.com")
    user_id: int = Field(..., title="User ID", example=123)
    user_title: str = Field(..., title="User Title", example="CAM")
    display_name: Optional[str] = Field(..., title="Display Name", example="A User")


class V2UserModelAgentView(V2UserModel):
    dc_theater: Optional[str] = Field(
        None,
        title="DC Theater",
        example="EMEA",
        description="The user's theater (AMER, APJGC, EMEA)",
    )


__all__ = ["V2UserModel", "V2UserModelAgentView"]
