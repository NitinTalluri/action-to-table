from typing import Literal, Annotated

import pytest
from pydantic import BaseModel, Field

from api.v2.models.workflows.macd import SchemaModelBase, ACATSchemaModel, \
    ACATToolAction
from api.v2.models.workflows.macd.registry import MACDSchemaRegistry, build_shim_model


class ModelA(BaseModel):
    data_type: Literal["A"]
    id: int

class ModelB(BaseModel):
    data_type: Literal["B"]
    id: int

ModelPayload = Annotated[ModelA | ModelB, Field(discriminator="data_type")]

class ModelC(BaseModel):
    id: int
    name: str | None = None
    
class ModelD(BaseModel):
    id: int | None = None
    name: str
    
ModelPolymorphicPayload = Annotated[ModelC | ModelD, Field()]


@pytest.mark.parametrize("model,expected", [
    (ModelA, False),
    (ModelB, False),
    (ModelPayload, True),
])
def test_annotation_detection(model, expected):
    from api.v2.models.workflows.macd.registry import is_annotation
    assert is_annotation(model) == expected, f"Expected {expected} for {model.__name__}"

@pytest.mark.parametrize("model", [ModelPayload])
def test_shim_model_creation(model):
    from api.v2.models.workflows.macd.registry import build_shim_model
    shim_model = build_shim_model(model, name=None)
    assert shim_model.__name__.startswith("ShimModel_"), "Shim model name does not start with 'ShimModel_'"
    assert shim_model.__name__ != "ShimModel_", "Shim model name should not be empty"
    shim_model_fields = shim_model.__fields__
    assert '__root__' in shim_model_fields, "Shim model does not have __root__ field"
    
@pytest.mark.parametrize("model,data,expected",[
    (ModelPayload, {"data_type": "A", "id": 1}, ModelA(data_type="A", id=1)),
    (ModelPayload, {"data_type": "B", "id": 2}, ModelB(data_type="B", id=2)),
])
def test_model_shim_validation(model, data, expected):
    from api.v2.models.workflows.macd.registry import build_shim_model
    shim_model = build_shim_model(model, name=None)
    validated_data = shim_model.parse_obj(data)
    assert hasattr(validated_data, '__root__'), "Validated data does not have __root__ attribute"
    assert validated_data.__root__ == expected, f"Expected {expected}, got {validated_data.__root__}"
    
    
@pytest.mark.parametrize("model", [ModelPayload])
def test_shim_model_schema(model):
    """Test that shim model makes a JSON schema correctly"""

    # schema  = schema_of(model)
    shim_model = build_shim_model(model, name=None)
    print(shim_model.schema_json(indent=4, ref_template="{model}"))
    
    schema = shim_model.schema(ref_template="{model}")
    assert "title" in schema, "Schema does not have a title"
    assert "discriminator" in schema, "Schema does not have a discriminator"
    assert "propertyName" in schema["discriminator"]
    assert "mapping" in schema["discriminator"]
    assert "oneOf" in schema, "Schema does not have a oneOf field"
    assert "definitions" in schema, "Schema does not have definitions"
    

def test_registry_polymorphic_call():
    """Create two models - one with a discriminator and one without."""
    
    test_registry = MACDSchemaRegistry()
    
    @test_registry
    class ClassLikeModel(ACATSchemaModel):
        id: int
        name: str
        tool_action: Literal["add_to_contract"] = "add_to_contract"
        
        
    class ACATVariantOne(ACATSchemaModel):
        instance_id: int
        serial_number: str | None = None
        tool_action: Literal["termination"] = Field(default="termination")
        
    class ACATVariantTwo(ACATSchemaModel):
        instance_id: int | None = None
        serial_number: str
        tool_action: Literal["termination"] = Field(default="termination")
        
    ACATUnionModel = Annotated[ACATVariantOne | ACATVariantTwo, Field()]
    test_registry(ACATUnionModel)
        
    assert len(test_registry.models) == 2
    
    print(test_registry.json())
    
    
    