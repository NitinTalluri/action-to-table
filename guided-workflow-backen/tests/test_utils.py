import pytest

from api.v2.models import V2CanvasParametersResponse, safe_parse_collection


def test_safe_parse_collection():
    # Limited scope testing, just to show the concept
    """
     canvas_id: int
    dc_engagement_id: int
    canvas_name: Optional[str] = Field("", example="MyCanvas")
    canvas_desc: Optional[str] = Field("", example="MyCanvas Short Description")
    canvas_type: Literal["sourced file canvas"] = Field(
        CanvasType.sourced_file_canvas.value, const=True, example="sourced file canvas"
    )
    files: list[V2SourcedCanvasFile]
    create_dtm: Optional[datetime]
    """

    data_ok = {
        "canvas_id": 1,
        "dc_engagement_id": 2,
        "canvas_name": "Test",
        "canvas_desc": "Test",
        "canvas_type": "sourced file canvas",
        "files": [
            {"name": "file1", "loc": "path1", "date": "2023-01-01"},
            {"name": "file2", "loc": "path2", "date": "2023-01-01"},
        ],
        "create_dtm": "2024-07-19T12:32:24.684000",
    }

    data_fail = {
        "canvas_id": None,
        "dc_engagement_id": 2,
        "canvas_name": "Test",
        "canvas_desc": "Test",
        "canvas_type": "sourced file canvas",
        "files": [123],
        "create_dtm": "2023-01-01",
    }

    collection = [data_ok, data_fail]

    parsed = safe_parse_collection(list[V2CanvasParametersResponse], collection)

    assert len(parsed) == 1
