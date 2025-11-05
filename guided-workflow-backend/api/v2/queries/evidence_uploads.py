from typing import TYPE_CHECKING, Optional

from sqlalchemy import func, literal_column, select, union_all

from api.v2.orm import V2UserDefinedType

if TYPE_CHECKING:
    from sqlmodel import Session

    from api.v2.models import V2CanvasEvidenceUploadResponse


def build_collector_select():
    from api.v2.orm import V2EvidenceCollectorHdr

    evidence_collector = (
        select(
            literal_column("request_id"),
            literal_column("effective_date"),
            literal_column("source"),
            literal_column("note"),
            literal_column("file_name_id"),
            literal_column("dc_engagement_id"),
            literal_column("'collector'").label("type"),
        )
        .select_from(V2EvidenceCollectorHdr)
        .where(func.nvl(V2EvidenceCollectorHdr.is_deleted, "F") == "F")
    )
    return evidence_collector


def build_customer_select():
    from api.v2.orm import V2EvidenceCustomerHdr

    evidence_customer = (
        select(
            literal_column("request_id"),
            literal_column("effective_date"),
            literal_column("source"),
            literal_column("note"),
            literal_column("file_name_id"),
            literal_column("dc_engagement_id"),
            literal_column("'customer'").label("type"),
        )
        .select_from(V2EvidenceCustomerHdr)
        .where(func.nvl(V2EvidenceCustomerHdr.is_deleted, "F") == "F")
    )
    return evidence_customer


def query_evidence_uploads(dc_engagement_id: Optional[int] = None):
    """
    Query customer/collector evidence uploads, optionally by dc_engagement_id.
    These are not user-specific
    """
    from api.v2.orm import (
        V2EvidenceCollectorHdr,
        V2EvidenceCustomerHdr,
    )

    evidence_collector = build_collector_select()
    evidence_customer = build_customer_select()

    if dc_engagement_id is not None:
        evidence_collector = evidence_collector.where(
            V2EvidenceCollectorHdr.dc_engagement_id == dc_engagement_id
        )
        evidence_customer = evidence_customer.where(
            V2EvidenceCustomerHdr.dc_engagement_id == dc_engagement_id
        )
    evidence_collector = evidence_collector.cte("evidence_collector")
    evidence_customer = evidence_customer.cte("evidence_customer")

    evidence = union_all(select(evidence_collector), select(evidence_customer)).cte(
        "evidence"
    )

    query = (
        select(
            evidence.c.request_id,
            evidence.c.effective_date,
            func.nvl(evidence.c.source, "").label("source"),
            func.nvl(evidence.c.note, "").label("note"),
            func.nvl(evidence.c.file_name_id, 0).label("file_name_id"),
            evidence.c.dc_engagement_id,
            evidence.c.type,
            func.nvl(V2UserDefinedType.value.label("file_name"), "No File Name").label(
                "file_name"
            ),
        )
        .select_from(evidence)
        .outerjoin(
            V2UserDefinedType,
            (evidence.c.file_name_id == V2UserDefinedType.id)
            & (V2UserDefinedType.is_deleted == "F"),
        )
    )

    return query


def get_evidence_uploads(
    dc_engagement_id: Optional[int], session: "Session"
) -> list["V2CanvasEvidenceUploadResponse"]:
    """Query, parse and return the evidence uploads"""

    stmt = query_evidence_uploads(dc_engagement_id=dc_engagement_id)
    db_evidence_uploads = session.execute(stmt).all()
    if not db_evidence_uploads:
        return []
    from api.v2.models import V2CanvasEvidenceUploadResponse, safe_parse_orm_collection

    evidence_uploads = safe_parse_orm_collection(
        list[V2CanvasEvidenceUploadResponse], db_evidence_uploads
    )
    return evidence_uploads
