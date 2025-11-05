from __future__ import annotations

from typing import Optional, Union

from pydantic.v1 import Field

from .. import Model, UiEnum


class ActionItem(Model):
    tree_id: int = Field(..., example=301)
    action_label: str = Field(..., example="Serial Tagging")
    ui_enum: Optional[Union[UiEnum, str]] = Field(
        ...,
        example="serial-tagging",
        description="Used for Front End Routing. When clicked, the front end will route to the corresponding page."
        "This type is unioned with a string to allow prevent misspellings and new routes from raising "
        "ValidationErrors.",
    )
    child_ids: Optional[list[int]] = Field(..., example=[])
