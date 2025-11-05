import json
import logging
from typing import Annotated

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import Integer, String, bindparam, text
from starlette.status import (
    HTTP_401_UNAUTHORIZED,
    HTTP_404_NOT_FOUND,
    HTTP_500_INTERNAL_SERVER_ERROR,
)

from api.dependencies import FlowV3ServiceDep, GetSessionDep, GetSettingsDep, GetUserDep
from api.v2.models import (
    TextMessageCreate,
    UiEnum,
    V2ArchivedFile,
    V2ArchivedFilesResponse,
    V2FileManagementChangeRequest,
    safe_parse_orm_collection,
)
from api.v2.orm import V2Engagement
from api.v2.queries import (
    query_referenced_canvas_id,
    query_users_engagements,
)
from api.v2.queries.information import get_schema_from_session, query_table_exists
from api.v2.services import ExternalServiceTracker

logger = logging.getLogger("api")

router = APIRouter()


file_management_tracker = ExternalServiceTracker(
    UiEnum.canvas_actions.value, "File Management"
)
FileManagementTracker = Annotated[
    ExternalServiceTracker, Depends(file_management_tracker)
]


def getpath(nested_dict, value, prepath=()):
    for k, v in nested_dict.items():
        path = (*prepath, k)
        if v == value:  # found value
            return path
        elif hasattr(v, "items"):  # v is a dict
            p = getpath(v, value, path)  # recursive call
            if p is not None:
                return p


def get_next_seq_val(conn):
    qry = text("""select DC_FILE_MANAGEMENT_SEQ.NEXTVAL""").bindparams()

    df = pd.read_sql(qry, conn)
    next_val = df["nextval"][0]

    return next_val


@router.get("/file_management_json/get_state")
def get_file_state_V2(
    dc_engagement_id: int,
    canvas_id: int,
    db_user: GetUserDep,
    session: GetSessionDep,
):
    """Get the tagsets and related tags for an engagement"""
    logged_user = db_user.cisco_cco_id

    user_engagements_query = query_users_engagements(logged_user).where(
        V2Engagement.dc_engagement_id == dc_engagement_id
    )

    user_engagement = session.exec(user_engagements_query).one_or_none()
    if not user_engagement:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"Engagement {dc_engagement_id} not found",
        )

    get_init_query = text(
        """select * from DC_FILE_MANAGEMENT_LIVEBOARDS where (liveboard_type_value in (:dc_engagement_id,:logged_user,'common'))
                                                and is_deleted = 'F' """
    ).bindparams(
        bindparam("dc_engagement_id", f"eng_{dc_engagement_id}", type_=Integer),
        bindparam("logged_user", logged_user, type_=String),
    )
    all_df = pd.read_sql(get_init_query, session.connection())

    common_pinboards = []
    custom_user_pinboards = []
    custom_eng_pinboards = []

    for _index, row in all_df.iterrows():
        if row["liveboard_type"] == "common":
            common_pinboards.append([row["display_name"], row["liveboard_id"]])
        if row["liveboard_type"] == "user":
            custom_user_pinboards.append([row["display_name"], row["liveboard_id"]])
        if row["liveboard_type"] == "engagement":
            custom_eng_pinboards.append([row["display_name"], row["liveboard_id"]])

    get_canvas_live_boards_query = text(
        """select * from DC_FILE_MANAGEMENT_LIVEBOARDS where CANVAS_ID =  :canvas_id
                                                and is_deleted = 'F' """
    ).bindparams(
        bindparam("canvas_id", canvas_id, type_=Integer),
    )
    canvas_liveboards_df = pd.read_sql(
        get_canvas_live_boards_query, session.connection()
    )
    attached_canvas_pinboards = []

    for _index, row in canvas_liveboards_df.iterrows():
        attached_canvas_pinboards.append([row["display_name"], row["liveboard_id"]])

    avail_init_json = {
        "currently_in_ts": {},
        "custom_eng": {},
        "custom_user": {},
        "delete": {},
        "common": {},
    }
    for i in custom_eng_pinboards:
        avail_init_json["custom_eng"][i[1]] = {"lb_params": {"display_name": i[0]}}
    for i in custom_user_pinboards:
        avail_init_json["custom_user"][i[1]] = {"lb_params": {"display_name": i[0]}}
    for i in common_pinboards:
        avail_init_json["common"][i[1]] = {"lb_params": {"display_name": i[0]}}
    for i in attached_canvas_pinboards:
        avail_init_json["currently_in_ts"][i[1]] = {"lb_params": {"display_name": i[0]}}

    print(avail_init_json)

    return avail_init_json


@router.post("/file_management_json/post_state", tags=["PrefectV3"])
async def set_file_state_V2(
    dc_engagement_id: int,
    canvas_id: int,
    payload: V2FileManagementChangeRequest,
    db_user: GetUserDep,
    session: GetSessionDep,
    prefect_service: FlowV3ServiceDep,
    settings: GetSettingsDep,
    tracker: FileManagementTracker,
    defer: bool = False,
):
    """

    Update the state of the liveboards in Thoughtspot, Custom User, Custom Engagement

    Note
    ----
    defer: bool = False
        If True, this request is related to a pending canvas create create. As such
        we will allow the flow that creates the canvas to handle calling the file management flow

    """
    logged_user = db_user.cisco_cco_id

    user_engagements_query = query_users_engagements(logged_user).where(
        V2Engagement.dc_engagement_id == dc_engagement_id
    )

    user_engagement = session.exec(user_engagements_query).one_or_none()
    if not user_engagement:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND, detail="Engagement not found"
        )

    qry = text(
        """select *, concat(LIVEBOARD_ID,'/', LIVEBOARD_TYPE,'/', DISPLAY_NAME) as concat_cols 
                from DC_FILE_MANAGEMENT_LIVEBOARDS where (liveboard_type_value in (:engagement_id,:requested_by,'common') or CANVAS_ID =  :canvas_id)
                                                and is_deleted = 'F'"""
    ).bindparams(
        bindparam("requested_by", f"{logged_user}", type_=String),
        bindparam("engagement_id", f"eng_{dc_engagement_id}", type_=String),
        bindparam("canvas_id", canvas_id, type_=Integer),
    )

    df = pd.read_sql(qry, session.connection())
    df.liveboard_id = df.liveboard_id.astype("int64")

    sf_set = set()
    for _index, row in df.iterrows():
        sf_set.add(row["concat_cols"])

    conversion_dict = {
        "currently_in_ts": "canvas",
        "custom_eng": "engagement",
        "custom_user": "user",
        "common": "common",
        "delete": "delete",
    }
    reverse_conversion_dict = {
        "canvas": "currently_in_ts",
        "engagement": "custom_eng",
        "user": "custom_user",
        "common": "common",
        "delete": "delete",
    }

    user_choice_set = set()
    new_state_json = payload.dict()

    for folder in new_state_json:
        for lb_id in new_state_json[folder]:
            user_choice_set.add(
                f"{lb_id}/{conversion_dict[folder]}/{new_state_json[folder][lb_id]['lb_params']['display_name']}"
            )

    changes = user_choice_set - sf_set

    new_changes_json = {
        "copy": {},
        "display_name_change": {},
        "delete": {},
    }

    for i in changes:
        lb_id = int(i.split("/")[0])
        lb_type = i.split("/")[1]
        display_name = i.split("/")[2]
        from_location = df["liveboard_type"][df["liveboard_id"] == int(lb_id)]
        if lb_id < 0:
            parent_lb_id = new_state_json[reverse_conversion_dict[lb_type]][str(lb_id)][
                "lb_params"
            ]["parent_id"]
            new_changes_json["copy"][parent_lb_id] = {
                "from": reverse_conversion_dict[lb_type],
                "to": reverse_conversion_dict[lb_type],
                "display_name": display_name,
            }
        elif lb_type == "delete":
            new_changes_json["delete"][lb_id] = {
                "from": reverse_conversion_dict[from_location.values[0]]
            }
        else:
            if from_location.values[0] == lb_type:
                new_changes_json["display_name_change"][lb_id] = {
                    "new_display_name": display_name
                }
            else:
                new_changes_json["copy"][lb_id] = {
                    "from": reverse_conversion_dict[from_location.values[0]],
                    "to": reverse_conversion_dict[lb_type],
                    "display_name": display_name,
                }

    request_id = tracker.get_next_request_id(session)

    file_management_log_query = text(
        """
    insert into DC_FILE_MANAGEMENT_RUNS(     REQUEST_ID,
                                                    CANVAS_NAME,
                                                    CHANGES_JSON,
                                                    RUN_ENV,
                                                    CREATE_DTM,
                                                    CREATED_BY,
                                                    STATUS
                                                    ) values ( :request_id,
                                                                :canvas_name,
                                                                :changes_json,
                                                                :run_env,
                                                                current_timestamp,
                                                                :requested_by,
                                                                :status
                                                                )
        """
    ).bindparams(
        bindparam("request_id", request_id, type_=Integer),
        bindparam("canvas_name", f"CANVAS-{canvas_id}", type_=String),
        bindparam(
            "changes_json",
            f"{json.dumps(new_changes_json, separators=(',', ':'))}",
            type_=String,
        ),
        bindparam("run_env", f"{settings.env!s}", type_=String),
        bindparam("requested_by", f"{logged_user}", type_=String),
        bindparam("status", "Pending", type_=String),
    )

    session.execute(file_management_log_query)
    session.commit()

    if defer:
        expected_canvas_table = f"CANVAS_{canvas_id}_THOUGHT_SPOT"
        db_schema = get_schema_from_session(session)
        table_exists_stmt = query_table_exists(expected_canvas_table, db_schema)
        table_exists = session.exec(table_exists_stmt).scalar_one()

        if not table_exists:
            logger.info("File Management : Canvas Id: %s - Deferring Event", canvas_id)
            return new_changes_json
        else:
            logger.info("File Management : Canvas Id: %s - Overriding Defer", canvas_id)

    logger.info("File Management : Canvas Id: %s - Emitting Event", canvas_id)

    notification_id = tracker.get_next_notification_id(session)

    params = {
        "env": settings.env,
        "canvas_id": canvas_id,
        "dc_user_id": db_user.user_id,
        "dc_engagement_id": dc_engagement_id,
        "notification_id": notification_id,
        "request_id": request_id,
    }

    db_background_job, db_notification = tracker.create_job(
        dc_engagement_id=dc_engagement_id,
        parameters=params,
        db_session=session,
        external_job_id="",
        workflow_data=new_changes_json,
        user_id=db_user.user_id,
        canvas_id=canvas_id,
        request_id=request_id,
        notification_id=notification_id,
    )

    try:
        prefect_service.emit_liveboard_management_requested(
            canvas_id=canvas_id,
            dc_user_id=db_user.user_id,
            dc_engagement_id=dc_engagement_id,
            notification_id=notification_id,
            request_id=request_id,
        )

        logger.info(
            "Emitted event 'liveboard_management_requested', request_id=%s logged_user=%s",
            request_id,
            logged_user,
        )
    except Exception as e:
        logger.error(
            "Error emitting event 'liveboard_management_requested', request_id=%s logged_user=%s",
            request_id,
            logged_user,
        )
        tracker.handle_job_error(
            db_session=session,
            db_notification=db_notification,
            message=TextMessageCreate(
                type="text",
                data=f"Encountered error while trying to schedule your request {request_id=}",
            ),
            exception=e,
        )
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error emitting event 'liveboard_management_requested'",
        ) from e

    session.commit()
    logger.info(new_changes_json)
    return new_changes_json


@router.get(
    "/archived/{dc_engagement_id}/{canvas_id}", response_model=V2ArchivedFilesResponse
)
def get_archived_files_for_canvas(
    dc_engagement_id: int,
    canvas_id: int,
    db_user: GetUserDep,
    session: GetSessionDep,
):
    """
    Get the list of archived files for a canvas
    """

    eng_canvas_query = query_referenced_canvas_id(
        dc_engagement_id=dc_engagement_id,
        canvas_id=canvas_id,
        dc_user_id=db_user.user_id,
    )
    eng_canvas = session.exec(eng_canvas_query).one_or_none()
    if not eng_canvas:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Not authorized to view this canvas",
        )

    query = text(
        """
        WITH 
        eng_backups AS (
            SELECT
                LIVEBOARD_ID, 
                DISPLAY_NAME,
                LOCATION, 
                'engagement' AS LB_TYPE,
                LIVEBOARD_TYPE_VALUE AS VALUE,
                CREATE_DTM
            FROM
                DC_FILE_MANAGEMENT_LIVEBOARDS
                WHERE LIVEBOARD_TYPE = 'backup'
                AND LIVEBOARD_TYPE_VALUE = :eng_type_value
                ),
        canvas_deleted AS (
            SELECT
                LIVEBOARD_ID,
                DISPLAY_NAME,
                LOCATION,
                'canvas' AS LB_TYPE,
                CANVAS_ID::VARCHAR AS VALUE,
                CREATE_DTM 
            FROM DC_FILE_MANAGEMENT_LIVEBOARDS
            WHERE IS_DELETED = 'T'
            AND CANVAS_ID IN (
            SELECT CANVAS_ID FROM DC_CANVAS_HDR WHERE DC_ENGAGEMENT_ID = :dc_engagement_id
            )),
        eng_deleted AS (
            SELECT
             LIVEBOARD_ID,
             DISPLAY_NAME,
             LOCATION,
             LIVEBOARD_TYPE AS LB_TYPE, 
             LIVEBOARD_TYPE_VALUE AS VALUE, 
             CREATE_DTM
            FROM DC_FILE_MANAGEMENT_LIVEBOARDS
            WHERE IS_DELETED = 'T'
            AND LIVEBOARD_TYPE_VALUE = :eng_type_value
            ),
        user_deleted AS (
            select LIVEBOARD_ID,
            DISPLAY_NAME,
            LOCATION, 
            LIVEBOARD_TYPE AS LB_TYPE, 
            LIVEBOARD_TYPE_VALUE AS VALUE, 
            CREATE_DTM
            FROM DC_FILE_MANAGEMENT_LIVEBOARDS
            WHERE IS_DELETED = 'T'
            AND LIVEBOARD_TYPE_VALUE = :user_liveboard_type           
        )
        SELECT * FROM eng_backups
        UNION
        SELECT * FROM canvas_deleted
        UNION
        SELECT * FROM eng_deleted
        UNION
        SELECT * FROM user_deleted
        ORDER BY CREATE_DTM DESC
        """
    )

    query = query.bindparams(
        bindparam("eng_type_value", value=f"eng_{dc_engagement_id}", type_=String),
        bindparam("dc_engagement_id", value=dc_engagement_id, type_=Integer),
        bindparam("user_liveboard_type", value=db_user.cisco_cco_id, type_=String),
    )

    db_result = session.exec(query).all()
    live_boards = safe_parse_orm_collection(list[V2ArchivedFile], db_result)

    return V2ArchivedFilesResponse(
        engagement_id=dc_engagement_id, canvas_id=canvas_id, live_boards=live_boards
    )
