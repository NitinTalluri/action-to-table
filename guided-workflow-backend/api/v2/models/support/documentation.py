from typing import Literal, Optional, Union

from pydantic.v1 import Field, conint

from . import Model, UiEnum


class DocLinkCreate(Model):
    doc_url: str = Field(..., description="The URL of the documentation")
    doc_desc: str = Field(..., description="A brief description of the documentation")
    doc_type: str = Field(..., description="The type of documentation")
    ui_enum: Optional[Union[UiEnum, str]] = Field(
        ..., description="The UI enum associated with the documentation link"
    )
    position: Optional[conint(ge=0)] = Field(
        None,
        description="The optional position of the documentation link. "
        "If not provided, the link will be appended to the end",
    )
    upload: Literal[False] = Field(default=False, const=True)


class DocLinkCreateUpload(DocLinkCreate):
    doc_url: Literal[None] = Field(None, description="The URL of the documentation")
    upload: Literal[True] = Field(default=True, const=True)


class DocumentationLinkCreate(Model):
    __root__: Union[DocLinkCreate, DocLinkCreateUpload] = Field(discriminator="upload")

    class Config:
        schema_extra = {
            "examples": [
                {
                    "doc_desc": "Example Video",
                    "doc_type": "video",
                    "ui_enum": "snif-report",
                    "upload": True,
                }
            ]
        }


class DocLinkCreateUpdate(DocLinkCreate):
    doc_url: Optional[str] = Field(
        None, description="The URL of the documentation, if changing"
    )
    doc_desc: Optional[str] = Field(
        None, description="A brief description of the documentation, if changing"
    )
    doc_type: Optional[str] = Field(
        None, description="The type of documentation, if changing"
    )
    ui_enum: Optional[Union[UiEnum, str]] = Field(
        None,
        description="The UI enum associated with the documentation link, if changing",
    )
    position: Optional[conint(ge=0)] = Field(
        None, description="The desired position of the documentation link if changing. "
    )
    upload: Literal[False] = Field(default=False, const=True, exclude=True)


class DocLinkCreateUploadUpdate(DocLinkCreateUpdate):
    doc_url: None = Field(None, description="The URL of the documentation")
    upload: Literal[True] = Field(default=True, const=True, exclude=True)


class DocumentationLinkUpdate(Model):
    __root__: Union[DocLinkCreateUpdate, DocLinkCreateUploadUpdate] = Field(
        discriminator="upload"
    )

    def dict(self, **kwargs):
        return self.__root__.dict(**kwargs)


class DocumentationLinkResponseModel(Model):
    doc_id: int = Field(..., description="The database ID of the documentation link")
    doc_url: str = Field(..., description="The URL of the documentation")
    doc_desc: str = Field(..., description="A brief description of the documentation")
    doc_type: str = Field(..., description="The type of documentation")
    ui_enum: Optional[Union[UiEnum, str]] = Field(
        ..., description="The UI enum associated with the documentation link"
    )
    position: int = Field(..., description="The position of the documentation link")
