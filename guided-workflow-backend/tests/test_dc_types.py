
from pydantic import parse_obj_as
from contextlib import nullcontext as does_not_raise
from api.v2.models import V2TableTypeMapping


def test_dc_types_routes(test_client):
    url = test_client.app.url_path_for("v2_get_dc_types")
    
    response = test_client.get(url)
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    data = response.json()
    with does_not_raise():
        parsed = parse_obj_as(list[V2TableTypeMapping], data)
        
        
def test_buying_programs_extra(test_client):
    url = test_client.app.url_path_for("v2_get_dc_types")
    
    response = test_client.get(url)
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    data = response.json()
    with does_not_raise():
        parsed = parse_obj_as(list[V2TableTypeMapping], data)
        
    buying_programs = next((table for table in parsed if table.table_name == "dc_buying_programs"), None)
    assert buying_programs is not None, "dc_buying_programs table not found in response"
    assert isinstance(buying_programs.mappings, list), "Mappings should be a list"
    buying_programs_mappings = buying_programs.mappings
    
    # Each mapping should have an 'extra' attribute that is a valid dict
    assert all(
        (table.extra is not None for table in buying_programs_mappings)
    )
    assert all(
    'is_default' in table.extra for table in buying_programs_mappings
    )
    assert len(
        [table for table in buying_programs_mappings if table.extra['is_default'] is True]
    ) == 1, "More than 1 default buying program found"
    
    
    