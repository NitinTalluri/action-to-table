import pytest
from pydantic.v1 import parse_obj_as
from sqlalchemy import text

from api.v2.models import (V3CanvasCreate, V2CanvasPredefinedFileNames,
                           V2CanvasParametersResponse, CanvasType)
from api.v2.queries import query_canvas_external_runs
from contextlib import nullcontext as does_not_raise

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
logger.addHandler(handler)


sample_bg_data = V3CanvasCreate(
    canvas_type="unified view canvas",
    canvas_name="test_query_canvas_external_runs",
    canvas_desc="test_query_canvas_external_runs",
    dc_engagement_id=94,
    files=[{
        "name": V2CanvasPredefinedFileNames.smart_account,
    }, {"name": V2CanvasPredefinedFileNames.mce}],
    tag_ids=[],
    current_snapshot_name=None,
    historical_snapshot_name="Snapshot 2024_12_20",
    customer_request_ids=[],
    collector_request_ids=[],
)
canvas_id = 999999 # Fake
request_id = 213157 # Manually created
@pytest.fixture
def loaded_sample_bg_data(db_session):
    stmt = text(
        """INSERT INTO
    DC_WF_BACKGROUND_JOB (CREATED_BY, CREATE_DTM, IS_DELETED, DC_ENGAGEMENT_ID, DC_USER_ID, WORKFLOW_ENUM,
                          WORKFLOW_DATA, CANVAS_ID, REQUEST_ID)
    VALUES
        ('test_query_canvas_external_runs',
         '2021-01-01 00:00:00',
         'F',
         :dc_engagement_id,
         423,
         'canvas-actions',
         :parameters,
         :canvas_id,
        :request_id
            )
         
        """
    ).bindparams(dc_engagement_id=sample_bg_data.dc_engagement_id, parameters=sample_bg_data.json(),
                 canvas_id=canvas_id,
                 request_id=request_id)
    db_session.execute(stmt)
    db_session.commit()
    yield db_session
    db_session.execute(text("DELETE FROM DC_WF_BACKGROUND_JOB WHERE REQUEST_ID = :request_id and CANVAS_ID = :canvas_id").bindparams(request_id=request_id, canvas_id=canvas_id))
    db_session.commit()

def test_query_canvas_external_runs(loaded_sample_bg_data):
    """
    Given a dc_wf_background_job entry, test that we correctly detect the version_ key
    and the query returns the data in a format expected by V2CanvasParametersResponse
    """
    
    query = query_canvas_external_runs(canvas_id=canvas_id)
    result = [param for param in [r.canvas_parameters for r in loaded_sample_bg_data.exec(query).all()] if param is not None]
    assert result is not None
    assert len(result) == 1
    with does_not_raise():
        parsed = parse_obj_as(list[V2CanvasParametersResponse], result)
    assert parsed is not None
    
@pytest.fixture()
def get_canvas_id(request, db_session):
    # Given a canvas type find a suitable canvas_id that has a corresponding entry in dc_wf_background_job
    canvas_type = getattr(request, "param", {}).get("canvas_type")
    if canvas_type is None:
        raise pytest.fail("canvas_type is required")
    
    stmt = text(
        """
        WITH ELIGIBLE_CANVAS_IDS AS (
            SELECT CANVAS_ID
            FROM DC_CANVAS_HDR
            WHERE CANVAS_TYPE = :canvas_type
            ),
        ELIGIBLE_BG_JOB_IDS AS (
            SELECT CANVAS_ID
            FROM DC_WF_BACKGROUND_JOB
            WHERE CANVAS_ID IN (SELECT CANVAS_ID FROM ELIGIBLE_CANVAS_IDS)
            AND WORKFLOW_DATA IS NOT NULL
            )
        SELECT DISTINCT CANVAS_ID
        FROM ELIGIBLE_BG_JOB_IDS
        LIMIT 1
        """
    ).bindparams(canvas_type=canvas_type)
    
    result = db_session.execute(stmt).scalar_one()
    return result, canvas_type
    
    

@pytest.mark.parametrize("get_canvas_id", [{"canvas_type": str(CanvasType.current_view_canvas)}, {"canvas_type": str(CanvasType.sourced_file_canvas)}], indirect=True)
def test_query_canvas_external_runs_legacy(db_session, get_canvas_id):
    """
    Given a dc_wf_background_job entry, test that we correctly detect the version_ key
    and the query returns the data in a format expected by V2CanvasParametersResponse
    """
    canvas_id, canvas_type = get_canvas_id
    logger.info("Using canvas_id: %s and canvas_type: %s", canvas_id, canvas_type)
    query = query_canvas_external_runs(canvas_id=canvas_id)
    result = [param for param in [r.canvas_parameters for r in db_session.exec(query).all()] if param is not None]
    assert result is not None
    with does_not_raise():
        parsed = parse_obj_as(list[V2CanvasParametersResponse], result)
    assert parsed is not None
    

    