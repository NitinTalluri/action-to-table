import logging
from functools import reduce
from operator import attrgetter
from typing import TYPE_CHECKING, Literal, Optional, TypedDict, Union

from sqlalchemy import Integer, String, select, text
from sqlalchemy.sql.elements import BindParameter
from toolz import compose_left, curry, excepts

from api.v2.models import (
    CanvasType,
    V2AcatLinkRead,
    V2CanvasEvidenceUploadResponse,
    V2CanvasPredefinedFileNames,
    V2EngagementLinks,
    V2MceLinkRead,
    V3CanvasCreate,
    V3CanvasRebuild,
)

if TYPE_CHECKING:
    from sqlmodel import Session


logger = logging.getLogger("api")


def _query_engagement_name(dc_engagement_id: int):
    stmt = (
        text(
            """
            SELECT
            :engagement_id as id,
            engagement_name as value,
            'engagement' as type
            FROM DC_ENGAGEMENT_HDR
            WHERE dc_engagement_id = :engagement_id
            """
        )
        .bindparams(engagement_id=dc_engagement_id)
        .columns(id=Integer, value=String, type=String)
    )
    return stmt


def _query_tag_ids(tag_ids: list[int]):
    stmt = (
        text(
            """
            SELECT
            tag_id as id,
            tag_name as value,
            'tag' as type
            FROM dc_tags
            WHERE tag_id IN :tag_ids
            """
        )
        .bindparams(BindParameter("tag_ids", expanding=True, value=tag_ids))
        .columns(id=Integer, value=String, type=String)
    )
    return stmt


def _query_evidence_files(dc_engagement_id):
    stmt = (
        text(
            """
            SELECT
            request_id as id,
            udt.value as value,
            'collector' as type
            FROM dc_evidence_collector_hdr collector
            JOIN dc_user_defined_type udt ON udt.id = collector.file_name_id
            WHERE udt.dc_engagement_id = :engagement_id
            UNION ALL
            SELECT
            request_id as id,
            udt.value as value,
            'customer' as type
            FROM dc_evidence_customer_hdr customer
            JOIN dc_user_defined_type udt ON udt.id = customer.file_name_id
            WHERE udt.dc_engagement_id = :engagement_id
            """
        )
        .bindparams(engagement_id=dc_engagement_id)
        .columns(id=Integer, value=String, type=String)
    )
    return stmt


def _canvas_current_readable_query(
    dc_engagement_id: int, tag_ids: list[int] | None, evidence_files: bool
):
    """
    Union together id, value, and type for lookups.
    'id' is the primary key of the source data.
    'value' is the human readable name of the source data.
    'type' is used to differentiate between different sources of data.
    """
    stmt = select(_query_engagement_name(dc_engagement_id).subquery())

    union_selects = []
    if tag_ids:
        union_selects.append(_query_tag_ids(tag_ids))
    if evidence_files:
        union_selects.append(
            _query_evidence_files(dc_engagement_id),
        )

    stmt = stmt.union(*union_selects)

    return stmt


def _get_readability_data(
    dc_engagement_id: int,
    tag_ids: Optional[list[int]],
    evidence_files: bool,
    session: "Session",
) -> dict[
    tuple[int, Literal["collector", "customer", "evidence_id", "engagement", "tag"]],
    str,
]:
    stmt = _canvas_current_readable_query(dc_engagement_id, tag_ids, evidence_files)
    result = session.exec(stmt).all()
    return {(row.id, row.type): row.value for row in result}


@curry
def with_label(label: str, value):
    return (label, value)


@curry
def get_with_default(keys, default, data):
    try:
        return reduce(getattr, keys, data) or default
    except:
        return default


@curry
def lookup_value(mapping, value_type, value):
    return mapping[value, value_type]


CanvasBaseReadable = TypedDict(
    "CanvasBaseReadable",
    {
        "Canvas Name": str,
        "Description": str,
        "Type": str,
    },
)


def canvas_base_readable(model: "V3CanvasCreate") -> CanvasBaseReadable:
    get_canvas_name = excepts(
        Exception,
        compose_left(attrgetter("canvas_name"), with_label("Canvas Name")),
        lambda _: with_label("Canvas Name", "Unknown"),
    )
    get_canvas_desc = excepts(
        Exception,
        compose_left(attrgetter("canvas_desc"), with_label("Description")),
        lambda _: with_label("Description", "Unknown"),
    )
    return dict(
        (
            get_canvas_name(model),
            get_canvas_desc(model),
            with_label("Type", str(model.canvas_type)),
        )
    )


def get_linked_sources_last_updated(
    model: "V3CanvasCreate",
) -> dict[str, list[str]]:
    """
    Given a canvas model, return a list of sources like:
    ACAT
        123, Updated: 2022-01-01
        124, Updated: 2022-01-01
    MCE
        Selected, No Links Found
    """

    def _format_link(row: Union[V2AcatLinkRead, V2MceLinkRead]) -> str | None:
        last_updated, row_id = row.last_updated, row.id
        return (
            f"{row_id}, Updated: {last_updated.strftime('%Y-%m-%d')}"
            if last_updated
            else f"{row_id}"
        )

    links = model._engagement_links
    if not links:
        return {}
    acat_links = links.acat_links
    mce_links = links.mce_links

    acat_fmt_links = [_format_link(row) for row in acat_links]
    mce_fmt_links = [_format_link(row) for row in mce_links]

    get_file_name = attrgetter("name")

    linked_sources = {}
    if acat_fmt_links and any(
        get_file_name(file) == V2CanvasPredefinedFileNames.acat for file in model.files
    ):
        linked_sources[V2CanvasPredefinedFileNames.acat.value] = acat_fmt_links
    if mce_fmt_links and any(
        get_file_name(file) == V2CanvasPredefinedFileNames.mce for file in model.files
    ):
        linked_sources[V2CanvasPredefinedFileNames.mce.value] = mce_fmt_links

    return linked_sources


def get_evidence_upload_readable(model: "V3CanvasCreate") -> dict[str, list[str]]:
    uploads = getattr(model, "_engagement_evidence_uploads", [])
    if not uploads:
        return {}

    def format_upload(upload: "V2CanvasEvidenceUploadResponse") -> str:
        return f"{upload.file_name}, #{upload.request_id}, Effective Date: {upload.effective_date.strftime('%Y-%m-%d')}"

    collector_files = (
        file
        for file in uploads
        if file.type == "collector" and file.request_id in model.collector_request_ids
    )
    customer_files = (
        file
        for file in uploads
        if file.type == "customer" and file.request_id in model.customer_request_ids
    )
    return {
        "Collector Files": [format_upload(file) for file in collector_files],
        "Customer Files": [format_upload(file) for file in customer_files],
    }


def canvas_unified_readable(
    model: "V3CanvasCreate", session: "Session"
) -> dict[str, str]:
    readability_data = _get_readability_data(
        dc_engagement_id=model.dc_engagement_id,
        tag_ids=model.tag_ids,
        evidence_files=bool(model.customer_request_ids or model.collector_request_ids),
        session=session,
    )

    base_readable = canvas_base_readable(model)

    get_engagement = excepts(
        Exception,
        compose_left(
            attrgetter("dc_engagement_id"),
            lookup_value(readability_data, "engagement"),
            with_label("Engagement"),
        ),
        lambda _: with_label("Engagement", "Unknown Engagement"),
    )

    _get_source = excepts(
        Exception,
        compose_left(
            attrgetter("name"),
        ),
        lambda _: "Unknown Source",
    )

    get_sources = excepts(
        Exception,
        compose_left(
            attrgetter("files"),
            lambda x: [_get_source(y) for y in x],
            with_label("Sources"),
        ),
        lambda _: with_label("Sources", []),
    )

    _get_tag_id = excepts(
        Exception,
        lookup_value(readability_data, "tag"),
        lambda e: f"Unnamed Tag #{e.args[0]}",
    )

    get_tag_ids = excepts(
        Exception,
        compose_left(
            attrgetter("tag_ids"),
            lambda x: [_get_tag_id(y) for y in x],
            lambda x: [y for y in x if y],
            with_label("Tag"),
        ),
        lambda _: with_label("Tags", []),
    )

    get_historical_snapshot_name = excepts(
        Exception,
        compose_left(
            attrgetter("historical_snapshot_name"),
            with_label("Historical Snapshot Name"),
        ),
        lambda _: with_label("Historical Snapshot Name", "None"),
    )

    linked_sources = get_linked_sources_last_updated(model=model)

    evidence_uploads = get_evidence_upload_readable(model=model)

    readable_data = dict(
        (
            get_engagement(model),
            get_sources(model),
            get_tag_ids(model),
            get_historical_snapshot_name(model),
        )
    )

    return {**base_readable, **readable_data, **linked_sources, **evidence_uploads}


def canvas_readable(
    model: Union[
        "V3CanvasRebuild",
        "V3CanvasCreate",
    ],
    session: "Session",
):
    """
    This function is used to convert the pydantic model into a human readable format.
    """

    match model.canvas_type:
        case CanvasType.unified_view_canvas:
            return canvas_unified_readable(model=model, session=session)
        case CanvasType.current_view_canvas:
            msg = f"Deprecated Canvas Type: {model.canvas_type}"
            logger.warning(msg)
            return {}
        case CanvasType.sourced_file_canvas:
            msg = f"Deprecated Canvas Type: {model.canvas_type}"
            logger.warning(msg)
            return {}
        case _:
            msg = f"Unknown Canvas Type: {model.canvas_type}"
            logger.warning(msg)
            return {}


__all__ = [
    "canvas_readable",
    "canvas_unified_readable",
]
