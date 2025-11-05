from sqlalchemy import case, func, literal, select, update


def query_documentation_append_position(wf_enum: str):
    """
    If the model to create does not have a position, this function will
    return a query that has the greatest position + 1
    """

    from api.v2.orm import DocumentationLinks

    stmt = (
        select(func.max(DocumentationLinks.position) + 1)
        .where(DocumentationLinks.ui_enum == wf_enum)
        .group_by(DocumentationLinks.ui_enum)
    )

    return stmt


def create_position_update_statement(
    wf_enum: str, prev_position: int, new_position: int, cisco_cco_id: str
):
    """
    Create an update statement that will set the position of all documentation links
    using the logic:

    - If the position == prev_position, set it to new_position
    - If the position <= new_position and position > prev_position, position = position - 1
    - If the position >= new_position and position < prev_position, position = position + 1

    """
    from api.v2.orm import DocumentationLinks

    updated_links = select(
        DocumentationLinks.doc_id,
        DocumentationLinks.position,
        case(
            (
                DocumentationLinks.position == prev_position,
                new_position,
            ),
            (
                (DocumentationLinks.position <= new_position)
                & (DocumentationLinks.position > prev_position),
                DocumentationLinks.position - 1,
            ),
            (
                (DocumentationLinks.position >= new_position)
                & (DocumentationLinks.position < prev_position),
                DocumentationLinks.position + 1,
            ),
            else_=DocumentationLinks.position,
        ).label("new_position"),
    ).where(DocumentationLinks.ui_enum == wf_enum)

    changed_links = select(
        updated_links.c.doc_id,
        updated_links.c.new_position,
        func.current_timestamp().label("update_dtm"),
        literal(cisco_cco_id).label("updated_by"),
    ).where(updated_links.c.position != updated_links.c.new_position)

    stmt = (
        update(DocumentationLinks)
        .where(DocumentationLinks.doc_id == changed_links.c.doc_id)
        .values(
            position=changed_links.c.new_position,
            update_dtm=changed_links.c.update_dtm,
            updated_by=changed_links.c.updated_by,
        )
    )
    return stmt


def create_position_insert_statement(wf_enum: str, position: int, cisco_cco_id: str):
    """
    Create an update statement that will set the position of all documentation links
    either +1 or no-op depending on the position of the new link
    """
    from api.v2.orm import DocumentationLinks

    updated_links = (
        select(
            DocumentationLinks.doc_id,
            DocumentationLinks.position,
            func.iff(
                DocumentationLinks.position >= position,
                DocumentationLinks.position + 1,
                DocumentationLinks.position,
            ).label("new_position"),
            func.iff(
                DocumentationLinks.position >= position,
                func.current_timestamp(),
                DocumentationLinks.update_dtm,
            ).label("update_dtm"),
            func.iff(
                DocumentationLinks.position >= position,
                cisco_cco_id,
                DocumentationLinks.updated_by,
            ).label("updated_by"),
        )
        .where(DocumentationLinks.ui_enum == wf_enum)
        .where(DocumentationLinks.is_deleted == "F")
    )

    stmt = (
        update(DocumentationLinks.__table__)
        .where(DocumentationLinks.__table__.c.doc_id == updated_links.c.doc_id)
        .values(
            position=updated_links.c.new_position,
            update_dtm=updated_links.c.update_dtm,
            updated_by=updated_links.c.updated_by,
        )
    )
    return stmt


__all__ = [
    "create_position_insert_statement",
    "create_position_update_statement",
    "query_documentation_append_position",
]
