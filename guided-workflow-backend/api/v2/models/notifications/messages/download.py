from typing import Literal

from pydantic.v1 import Field

from . import MessageType, Model


class DownloadData(Model):
    label: str = Field(
        ..., description="The label of the download.", example="Download Report"
    )
    url: str = Field(
        ..., description="The URL of the download.", example="s3://results/report.csv"
    )


class DownloadMessage(Model):
    type: Literal["download"] = Field(MessageType.download.value, const=True)
    data: DownloadData

    class Config:
        schema_extra = {
            "examples": [
                {
                    "type": "download",
                    "data": {
                        "label": "Download Report",
                        "url": "s3://results/report.csv",
                    },
                }
            ]
        }
