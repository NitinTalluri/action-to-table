from typing import Optional, TypedDict

from sqlalchemy import (
    Integer,
    TextualSelect,
    and_,
    bindparam,
    case,
    distinct,
    func,
    or_,
    text,
    type_coerce,
)
from sqlmodel import select

from api.v2.orm.json_varchar import JSONVarchar
from api.v2.queries.parse_json_into_table import lateral_flatten


def build_canvas_select(
    canvas_id: Optional[int] = None, dc_engagement_id: Optional[int] = None
):
    from api.v2.orm import V2Canvas

    canvas_select = (
        select(
            func.concat(V2Canvas.canvas_name, " (", V2Canvas.canvas_id, ")").label(
                "canvas"
            ),
            V2Canvas.dc_engagement_id,
            V2Canvas.canvas_id,
        )
        .where(V2Canvas.is_deleted == "F")
        .where(~V2Canvas.canvas_name.ilike("%DEACTIVATED%"))
    )

    if canvas_id:
        canvas_select = canvas_select.where(V2Canvas.canvas_id == canvas_id)
    if dc_engagement_id:
        canvas_select = canvas_select.where(
            V2Canvas.dc_engagement_id == dc_engagement_id
        )

    return canvas_select


def build_instances_select(
    canvas_id: Optional[int] = None,
    dc_engagement_id: Optional[int] = None,
    dc_user_id: Optional[int] = None,
):
    from api.v2.orm import V2ThoughtSpotInstanceRequests

    api_processed = or_(
        *[
            V2ThoughtSpotInstanceRequests.updated_by.ilike(s)
            for s in ("request_id%", "exec_by%")
        ]
    )

    extract_state = case(
        (
            (api_processed & V2ThoughtSpotInstanceRequests.is_deleted == "T"),
            "processed",
        ),
        (V2ThoughtSpotInstanceRequests.is_deleted == "F", "pending"),
        (V2ThoughtSpotInstanceRequests.is_deleted == "T", "deleted"),
        else_="deleted",
    )

    # noinspection PyArgumentList
    instances_select = (
        select(
            V2ThoughtSpotInstanceRequests.thoughtspot_id,
            V2ThoughtSpotInstanceRequests.dc_engagement_id,
            V2ThoughtSpotInstanceRequests.user_id,
            V2ThoughtSpotInstanceRequests.tag_ids,
            V2ThoughtSpotInstanceRequests.tagset_ids,
            V2ThoughtSpotInstanceRequests.comment,
            V2ThoughtSpotInstanceRequests.user_action,
            V2ThoughtSpotInstanceRequests.canvas_id,
            V2ThoughtSpotInstanceRequests.count_instances,
            V2ThoughtSpotInstanceRequests.file_location,
            V2ThoughtSpotInstanceRequests.create_dtm,
            V2ThoughtSpotInstanceRequests.created_by,
            V2ThoughtSpotInstanceRequests.updated_by,
            V2ThoughtSpotInstanceRequests.is_deleted,
            extract_state.label("extract_state"),
        )
        .where(V2ThoughtSpotInstanceRequests.file_location.isnot(None))
        .where(text("extract_state != 'deleted'"))
    )

    if canvas_id:
        instances_select = instances_select.where(
            V2ThoughtSpotInstanceRequests.canvas_id == canvas_id
        )
    if dc_engagement_id:
        instances_select = instances_select.where(
            V2ThoughtSpotInstanceRequests.dc_engagement_id == dc_engagement_id
        )
    if dc_user_id:
        instances_select = instances_select.where(
            V2ThoughtSpotInstanceRequests.user_id == dc_user_id
        )

    return instances_select


def build_user_assoc_engagement_select(dc_user_id: Optional[int] = None):
    from api.v2.orm import V2CamEngagement, V2Engagement, V2User

    users_engagement_select = (
        select(
            V2Engagement.dc_engagement_id,
        )
        .join(
            V2CamEngagement,
            and_(
                V2Engagement.dc_engagement_id == V2CamEngagement.dc_engagement_id,
                V2CamEngagement.is_deleted == "F",
            ),
        )
        .join(
            V2User,
            and_(
                V2CamEngagement.user_id == V2User.user_id,
                V2User.is_deleted == "F",
            ),
        )
        .where(V2Engagement.is_deleted == "F")
    )

    if dc_user_id:
        users_engagement_select = users_engagement_select.where(
            V2User.user_id == dc_user_id
        )

    return users_engagement_select


def build_valid_tag_ids_select(
    dc_engagement_id: Optional[int] = None,
):
    from api.v2.orm import V2Tags, V2Tagset

    # noinspection PyTypeChecker

    eng_filter = {1, dc_engagement_id} if dc_engagement_id else {1}

    tagset_ids_cte = select(V2Tagset.tagset_id, V2Tagset.tagset_name).where(
        V2Tagset.is_deleted == "F"
    )

    if dc_engagement_id:
        tagset_ids_cte = tagset_ids_cte.where(V2Tagset.dc_engagement_id.in_(eng_filter))

    tagset_ids_cte = tagset_ids_cte.cte("valid_tagsets")

    # noinspection PyTypeChecker
    tag_ids_select = (
        select(
            V2Tags.tag_id,
            V2Tags.tagset_id,
            V2Tags.tag_name,
            tagset_ids_cte.c.tagset_name.label("tagset_name"),
        )
        .join(
            tagset_ids_cte,
            V2Tags.tagset_id == tagset_ids_cte.c.tagset_id,
        )
        .where(V2Tags.is_deleted == "F")
    )

    return tag_ids_select, tagset_ids_cte


def build_canvas_source(
    canvas_id: Optional[int] = None,
    dc_engagement_id: Optional[int] = None,
    dc_user_id: Optional[int] = None,
):
    canvas_select = build_canvas_select(canvas_id, dc_engagement_id).cte()
    instances_select = build_instances_select(canvas_id, dc_engagement_id).cte()
    cam_engagement_select = build_user_assoc_engagement_select(dc_user_id).cte()

    # noinspection PyArgumentList
    canvas_cte = (
        select(
            canvas_select.c.canvas,
            canvas_select.c.dc_engagement_id,
            instances_select.c.thoughtspot_id,
            instances_select.c.user_id,
            instances_select.c.tag_ids,
            instances_select.c.tagset_ids,
            instances_select.c.comment,
            instances_select.c.user_action,
            instances_select.c.canvas_id,
            instances_select.c.count_instances,
            instances_select.c.file_location,
            instances_select.c.create_dtm,
            instances_select.c.created_by,
            instances_select.c.extract_state,
        )
        .join(
            instances_select,
            (canvas_select.c.dc_engagement_id == instances_select.c.dc_engagement_id)
            & (canvas_select.c.canvas_id == instances_select.c.canvas_id),
        )
        .join(
            cam_engagement_select,
            canvas_select.c.dc_engagement_id
            == cam_engagement_select.c.dc_engagement_id,
        )
        .where(canvas_select.c.dc_engagement_id.isnot(None))
    )

    if dc_user_id:
        canvas_cte = canvas_cte.where(instances_select.c.user_id == dc_user_id)

    canvas_cte = canvas_cte.cte("canvas_requests")

    return canvas_cte


def build_thoughtspot_tagging_query(
    canvas_id: Optional[int] = None,
    dc_engagement_id: Optional[int] = None,
    dc_user_id: Optional[int] = None,
):
    """
    Using canvas source, use a lateral flatten and parse json to:

    1. If user_action == 'set'
        1. Join tag_ids to valid tag ids and get names
        2. Join tagset_ids to valid tagset ids and get names
    2. If user_action == 'unset'
        1. tag_ids is null and the tag name is 'unset'
        2. Join tagset_ids to valid tagset ids and get names
    3. If user_action == 'extract'
        1. tag_ids is null and the tag name is null
        2. tagset_ids is null and the tagset name is null

    ----------------------------------------------------------------
    Finally, join to canvas CTE where the canvas is not deleted AND the canvas does not
      contain the substring (DEACTIVATED) in the canvas name

    """

    canvas_cte = build_canvas_source(canvas_id, dc_engagement_id, dc_user_id)

    valid_tags, valid_tagset_cte = build_valid_tag_ids_select(dc_engagement_id)
    valid_tags = valid_tags.cte("valid_tags")

    set_action_query = (
        select(
            canvas_cte.c.thoughtspot_id,
            func.parse_json(canvas_cte.c.tag_ids).label("tag_ids"),
        )
        .where(canvas_cte.c.user_action == "set")
        .cte("set_action")
    )

    flat_tags = lateral_flatten(set_action_query.c.tag_ids).table_valued(
        "value", joins_implicitly=True
    )
    # noinspection PyTypeChecker,PydanticTypeChecker
    left_tags = (
        select(
            set_action_query.c.thoughtspot_id,
            flat_tags,
        )
        .select_from(set_action_query)
        .distinct()
        .cte("left_tags")
    )
    # noinspection PyArgumentList
    left_named_tags = (
        select(
            left_tags.c.thoughtspot_id,
            left_tags.c.value.label("tag_id"),
            valid_tags.c.tag_name.label("tag_name"),
            valid_tags.c.tagset_id.label("tagset_id"),
            valid_tags.c.tagset_name.label("tagset_name"),
        )
        .join(valid_tags, left_tags.c.value == valid_tags.c.tag_id)
        .cte("left_named_tags")
    )

    # noinspection PyArgumentList
    tag_grps = (
        select(
            left_named_tags.c.thoughtspot_id,
            func.array_agg(left_named_tags.c.tag_id).label("tag_ids"),
            func.array_agg(distinct(left_named_tags.c.tag_name)).label("tag_names"),
            func.array_agg(distinct(left_named_tags.c.tagset_id)).label("tagset_ids"),
            func.array_agg(distinct(left_named_tags.c.tagset_name)).label(
                "tagset_names"
            ),
        )
        .group_by(left_named_tags.c.thoughtspot_id)
        .cte("tag_grps")
    )

    unset_action_query = (
        select(
            canvas_cte.c.thoughtspot_id,
            func.parse_json(canvas_cte.c.tagset_ids).label("tagset_ids"),
        )
        .where(canvas_cte.c.user_action == "unset")
        .subquery()
    )

    flat_tagsets = lateral_flatten(unset_action_query.c.tagset_ids).table_valued(
        "value", joins_implicitly=True
    )

    # noinspection PyTypeChecker,PydanticTypeChecker
    left_tagsets = (
        select(
            unset_action_query.c.thoughtspot_id,
            flat_tagsets,
        )
        .select_from(unset_action_query)
        .distinct()
        .cte("left_tagsets")
    )

    real_named_tagsets = (
        select(
            left_tagsets.c.thoughtspot_id,
            valid_tagset_cte.c.tagset_id,
            valid_tagset_cte.c.tagset_name,
        )
        .join(valid_tagset_cte, left_tagsets.c.value == valid_tagset_cte.c.tagset_id)
        .cte("left_named_tagsets")
    )

    tagset_grps = (
        select(
            real_named_tagsets.c.thoughtspot_id,
            func.array_agg(real_named_tagsets.c.tagset_id).label("tagset_ids"),
            func.array_agg(distinct(real_named_tagsets.c.tagset_name)).label(
                "tagset_names"
            ),
        )
        .group_by(real_named_tagsets.c.thoughtspot_id)
        .cte("tagset_grps")
    )

    # Almost done, now ues a join for the final result
    empty_list = func.to_json(func.array_construct())
    json_array = lambda c: func.to_json(func.array_construct_compact(c))
    to_json = lambda c: func.to_json(c)

    # noinspection PyTypeChecker,PyArgumentList
    final_result = (
        select(
            canvas_cte.c.canvas,
            canvas_cte.c.dc_engagement_id,
            canvas_cte.c.thoughtspot_id,
            canvas_cte.c.user_id,
            canvas_cte.c.user_action,
            canvas_cte.c.extract_state,
            type_coerce(
                func.iff(
                    canvas_cte.c.user_action == "set",
                    to_json(tag_grps.c.tag_ids),
                    empty_list,
                ),
                JSONVarchar,
            ).label("tag_ids"),
            type_coerce(
                func.iff(
                    canvas_cte.c.user_action == "set",
                    to_json(tag_grps.c.tag_names),
                    json_array(canvas_cte.c.user_action),
                ),
                JSONVarchar,
            ).label("tag_names"),
            type_coerce(
                (
                    case(
                        (
                            canvas_cte.c.user_action == "set",
                            to_json(tag_grps.c.tagset_ids),
                        ),
                        (
                            canvas_cte.c.user_action == "unset",
                            to_json(tagset_grps.c.tagset_ids),
                        ),
                        (canvas_cte.c.user_action == "extract", empty_list),
                        else_=empty_list,
                    )
                ),
                JSONVarchar,
            ).label("tagset_ids"),
            type_coerce(
                (
                    case(
                        (
                            canvas_cte.c.user_action == "set",
                            to_json(tag_grps.c.tagset_names),
                        ),
                        (
                            canvas_cte.c.user_action == "unset",
                            to_json(tagset_grps.c.tagset_names),
                        ),
                        (
                            canvas_cte.c.user_action == "extract",
                            empty_list,
                        ),
                        else_=empty_list,
                    )
                ),
                JSONVarchar,
            ).label("tagset_names"),
            canvas_cte.c.comment,
            canvas_cte.c.canvas_id,
            canvas_cte.c.count_instances,
            canvas_cte.c.file_location,
            canvas_cte.c.create_dtm,
            canvas_cte.c.created_by,
        )
        .outerjoin(tag_grps, canvas_cte.c.thoughtspot_id == tag_grps.c.thoughtspot_id)
        .outerjoin(
            tagset_grps, canvas_cte.c.thoughtspot_id == tagset_grps.c.thoughtspot_id
        )
    )

    return final_result


def _make_thoughtspot_engagement_query(
    thoughtspot_ids: set[int], dc_user_id: int
) -> TextualSelect:
    """
    Build SQLAlchemy text query with bindparams for thoughtspot engagement mapping.
    """
    stmt = (
        text("""
        SELECT dc_engagement_id, thoughtspot_id
        FROM dc_thoughtspot_instance_requests
        WHERE thoughtspot_id IN :thoughtspot_ids
        AND is_deleted = 'F'
        AND user_id = :dc_user_id
        AND user_action IN ('set', 'unset')
    """)
        .bindparams(
            bindparam("thoughtspot_ids", list(thoughtspot_ids), expanding=True),
            bindparam("dc_user_id", dc_user_id),
        )
        .columns(dc_engagement_id=Integer, thoughtspot_id=Integer)
    )

    return stmt


class TaskEngagementRow(TypedDict):
    dc_engagement_id: int
    thoughtspot_id: int


def get_thoughtspot_tasks_engagement(
    thoughtspot_ids: set[int], user_id: int, session
) -> list[TaskEngagementRow] | None:
    """
    Execute the thoughtspot engagement mapping query.
    """
    stmt = _make_thoughtspot_engagement_query(thoughtspot_ids, user_id)

    result = session.exec(stmt).all()
    if not result:
        return None

    return [
        TaskEngagementRow(
            dc_engagement_id=row.dc_engagement_id, thoughtspot_id=row.thoughtspot_id
        )
        for row in result
    ]


__all__ = ["build_thoughtspot_tagging_query", "get_thoughtspot_tasks_engagement"]
