import hypothesis
import hypothesis.strategies as st
from hypothesis import given, assume
from pydantic.v1 import create_model, parse_obj_as


from api.v2.models.workflows.macd.ccwr import CCWRSwapSerialInstanceSchemaModel
from api.v2.models.workflows.macd.registry import build_shim_model


target_model = build_shim_model(CCWRSwapSerialInstanceSchemaModel, "CCWRSwapSerialInstanceSchemaModelS")



@st.composite
def model_strategy(draw):
    
    source_instance_id_st=st.one_of(st.just(1),    st.none())
    source_serial_number_st=st.one_of(st.just("SN123456"), st.none())
    target_instance_id_st=st.one_of(st.just(2), st.none())
    target_serial_number_st=st.one_of(st.just("SN654321"), st.none())
    source_instance_id = draw(source_instance_id_st)
    source_serial_number = draw(source_serial_number_st)
    target_instance_id = draw(target_instance_id_st)
    target_serial_number = draw(target_serial_number_st)
    
    assume(not all((v is None for v in (source_instance_id, source_serial_number))))
    assume(not all((v is None for v in (target_instance_id, target_serial_number))))
    
    # noinspection PyTypeChecker
    model_obj = parse_obj_as(target_model,
        {"__root__": {
            "source_instance_id": source_instance_id,
            "source_serial_number": source_serial_number,
            "target_instance_id": target_instance_id,
            "target_serial_number": target_serial_number,
            "rma_number": "RMA123456",
        }}
    )
    return model_obj
    
    
    
@given(model_obj=model_strategy())
def test_model_parsing(model_obj):
    model = model_obj.__root__
    
    # Must have at least one source
    sources = [s for s in [model.source_instance_id, model.source_serial_number] if s is not None]
    assert len(sources) >= 1
    
    # Must have exactly one target
    targets = [s for s in [model.target_instance_id, model.target_serial_number] if s is not None]
    assert len(targets) >= 1
    
    print(model.dict(include={"source_instance_id", "source_serial_number", "target_instance_id", "target_serial_number"}))