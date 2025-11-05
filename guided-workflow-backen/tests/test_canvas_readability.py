from operator import attrgetter

from hypothesis import strategies as st, given, settings, assume, HealthCheck
from hypothesis.strategies import composite
from sqlmodel import Session

from api.v2.models import V2CanvasPredefinedFileNames, V3CanvasCreate, CanvasType
from api.v2.models.canvas import V2CanvasPredefinedFiles
from api.v2.services.readability.canvas import (canvas_unified_readable,
                                                )


@composite
def canvas_unified_strategy(draw):
    canvas_name = draw(st.just("MyCanvas"))
    canvas_desc = draw(st.just("MyCanvas Short Description"))
    dc_engagement_id = draw(st.just(94))
    files = draw(
        st.lists(st.builds(
            V2CanvasPredefinedFiles, name=st.sampled_from(list(V2CanvasPredefinedFileNames))), unique_by=lambda x: x.name))
    
    tag_ids = draw(st.lists(st.sampled_from([2002233, 2002234]), unique=True))
    customer_files = draw(st.lists(st.sampled_from([211856, 211865]), unique=True))
    collector_files = draw(st.lists(st.sampled_from([212927, 212302]), unique=True))
    
    historical_snapshot_name = draw(st.sampled_from(["Snapshot 2024_12_20", "Snapshot 2024_12_06", None]))
    current_snapshot_name = draw(st.sampled_from(["Snapshot 2024_12_20", "Snapshot 2024_12_06", None]))
    
    assume(historical_snapshot_name != current_snapshot_name)
    assume(current_snapshot_name is None or historical_snapshot_name is not None)
    
    return V3CanvasCreate(
        canvas_type=CanvasType.unified_view_canvas,
        canvas_name=canvas_name,
        canvas_desc=canvas_desc,
        dc_engagement_id=dc_engagement_id,
        files=files,
        tag_ids=tag_ids,
        historical_snapshot_name=historical_snapshot_name,
        current_snapshot_name=current_snapshot_name,
        customer_request_ids=customer_files,
        collector_request_ids=collector_files,
    )

@composite
def linked_sources(draw):
    acat_ids = draw(st.lists(st.integers(min_value=1, max_value=100000), unique=True))
    mce_ids = draw(st.lists(st.integers(min_value=1, max_value=100000), unique=True))
    party_ids = draw(st.lists(st.integers(min_value=1, max_value=100000), unique=True))
    smart_ids = draw(st.lists(st.integers(min_value=1, max_value=100000), unique=True))
    
    return acat_ids, mce_ids, party_ids, smart_ids
    



@given(data=st.data())
@settings(max_examples=10, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_canvas_next_readable(data, mocker):
    model: "V3CanvasCreate" = data.draw(canvas_unified_strategy())
    acat_ids, mce_ids, party_ids, smart_ids = data.draw(linked_sources())

    from api.dependencies.database import get_engine
    from api.dependencies import get_settings

    engine = get_engine(get_settings())
    
    get_file_name = attrgetter("name")
    expected_links = {}
    if acat_ids and any(get_file_name(file) == V2CanvasPredefinedFileNames.acat for file in model.files):
        expected_links[V2CanvasPredefinedFileNames.acat.value] = [f"{id} - 2000-01-01" for id in acat_ids]
    if mce_ids and any(get_file_name(file) == V2CanvasPredefinedFileNames.mce for file in model.files):
        expected_links[V2CanvasPredefinedFileNames.mce.value] = [f"{id} - 2000-01-01" for id in mce_ids]
        
    
    
    mocked_func = mocker.MagicMock(return_value=expected_links)
    
    with mocker.patch('api.v2.services.readability.canvas.get_linked_sources_last_updated', new=mocked_func):
        with Session(engine) as session:
            readable = canvas_unified_readable(model, session)
        
    assert 'Canvas Name' in readable, 'Canvas Name not found in readable'
    assert readable['Canvas Name'] == model.canvas_name, 'Canvas Name does not match'
    assert 'Description' in readable, 'Description not found in readable'
    assert readable['Description'] == model.canvas_desc, 'Description does not match'
    assert 'Engagement' in readable, 'Engagement not found in readable'
    assert isinstance(readable['Engagement'], str), 'Engagement is not a string'
    assert 'Sources' in readable, 'Sources not found in readable'
    assert len(readable['Sources']) == len(model.files), 'Sources length does not match'
    assert 'Tag' in readable, 'Tag not found in readable'
    assert len(readable['Tag']) == len(model.tag_ids), 'Tag length does not match'
    assert 'Customer Files' in readable, 'Customer Files not found in readable'
    assert len(readable['Customer Files']) == len(model.customer_request_ids), 'Customer Files length does not match'
    assert 'Collector Files' in readable, 'Collector Files not found in readable'
    assert len(readable['Collector Files']) == len(model.collector_request_ids), 'Collector Files length does not match'
    assert 'Historical Snapshot Name' in readable, 'Historical Snapshot Name not found in readable'
    assert readable['Historical Snapshot Name'] == model.historical_snapshot_name
    
    
    assert mocked_func.called, 'get_linked_sources_last_updated not called'
    
    if 'ACAT' in expected_links:
        assert 'ACAT' in readable, 'ACAT not found in readable'
        assert len(readable['ACAT']) == len(expected_links['ACAT']), 'ACAT length does not match'
    else:
        assert 'ACAT' not in readable, 'ACAT found in readable'
    if 'MCE' in expected_links:
        assert 'MCE' in readable, 'MCE not found in readable'
        assert len(readable['MCE']) == len(expected_links['MCE']), 'MCE length does not match'
    else:
        assert 'MCE' not in readable, 'MCE found in readable'
        
    
        
    print(readable)
    
    


