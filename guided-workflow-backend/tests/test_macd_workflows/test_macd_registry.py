import pytest

from api.v2.models.workflows.macd import AMRRToolAction, CCWRToolAction, ACATToolAction

def test_macd_registry_response(test_client):
    """Test the MACD schemas endpoint"""
    try:
        url = test_client.app.url_path_for("get_macd_schemas")
    except Exception as e:
        raise pytest.fail(f"Failed to get URL path for 'get_macd_schema': {e}")
    
    response = test_client.get(url)
    assert response.status_code == 200
    schemas = response.json()
    assert isinstance(schemas, list), "Response is not a list"
    
    from api.v2.models.workflows.macd import ToolName
    
    tool2action = {
        ToolName.amrr: AMRRToolAction,
        ToolName.ccwr: CCWRToolAction,
        ToolName.acat: ACATToolAction,
    }
    
    seen_tool_actions = {}
    
    property_schemas = [schema for schema in schemas if "properties" in schema]
    union_schemas = [schema for schema in schemas if "anyOf" in schema]
    
    for schema in property_schemas:
        schema_properties = schema.get("properties")
        assert "tool_name" in schema_properties, "Schema missing tool_name"
        assert "tool_action" in schema_properties, "Schema missing tool_action"
        
        tool_name = schema_properties["tool_name"]['enum'][0]
        tool_action = schema_properties["tool_action"]['enum'][0]
        
        try:
            tool_enum = ToolName(tool_name)
        except ValueError as e:
            raise pytest.fail(f"Invalid tool name in schema: {tool_name}. Error: {e}")
            
        try:
            action_enum = tool2action[tool_enum](tool_action)
        except ValueError as e:
            raise pytest.fail(f"Invalid action for tool {tool_name}: {tool_action}. Error: {e}")
            
        if tool_enum not in seen_tool_actions:
            seen_tool_actions[tool_enum] = set()
            
        seen_tool_actions[tool_enum].add(action_enum)
    
    for schema in union_schemas:
        schema_any_of = schema.get("anyOf")
        assert schema_any_of, "Schema missing anyOf"
        schema_definitions = schema.get("definitions", {})
        
        for sub_schema in schema_any_of:
            if "$ref" in sub_schema:
                ref_name = sub_schema["$ref"]
                assert ref_name in schema_definitions, f"Reference {ref_name} not found in definitions"
                
                sub_schema_properties = schema_definitions[ref_name].get("properties", {})
                assert "tool_name" in sub_schema_properties, f"Schema {ref_name} missing tool_name"
                assert "tool_action" in sub_schema_properties, f"Schema {ref_name} missing tool_action"
                
                tool_name = sub_schema_properties["tool_name"]['enum'][0]
                tool_action = sub_schema_properties["tool_action"]['enum'][0]
                
                try:
                    tool_enum = ToolName(tool_name)
                except ValueError as e:
                    raise pytest.fail(f"Invalid tool name in schema: {tool_name}. Error: {e}")
                    
                try:
                    action_enum = tool2action[tool_enum](tool_action)
                except ValueError as e:
                    raise pytest.fail(f"Invalid action for tool {tool_name}: {tool_action}. Error: {e}")
                    
                if tool_enum not in seen_tool_actions:
                    seen_tool_actions[tool_enum] = set()
                    
                seen_tool_actions[tool_enum].add(action_enum)
        
        
        
    
    # Verify all tools and actions are present
    for tool, action_enum in tool2action.items():
        expected_actions = set(action_enum.__members__.values())
        actual_actions = seen_tool_actions.get(tool, set())
        missing_actions = expected_actions - actual_actions
        assert not missing_actions, f"Missing actions for {tool}: {missing_actions}"

def get_response(url, test_client):
    return test_client.get(url).json()
    

def test_macd_response_benchmark(test_client, benchmark):
    """Test the MACD schemas endpoint for performance"""
    try:
        url = test_client.app.url_path_for("get_macd_schemas")
    except Exception as e:
        raise pytest.fail(f"Failed to get URL path for 'get_macd_schema': {e}")
    
    result = benchmark(get_response, url, test_client)
    
    
    
    