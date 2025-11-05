from hypothesis import given, strategies as st, assume
from hypothesis.strategies import composite

from api.v2.models import V3CanvasCreate, V2CanvasPredefinedFileNames, V3CanvasRebuild
from api.v2.models.canvas import V2CanvasPredefinedFiles


@composite
def canvas_strategy(draw):
    files = draw(
        st.lists(
            st.builds(
                V2CanvasPredefinedFiles,
                name=st.sampled_from(list(V2CanvasPredefinedFileNames))
            )
        )
    )
    model = draw(
        st.builds(
            V3CanvasCreate,
            files=st.just(files)
        )
    )
    assume(len(model.files))
    return model

@given(canvas_create=canvas_strategy())
def test_build_canvas_create_validate_files(canvas_create):
    
    assert V2CanvasPredefinedFileNames.baseline_tags not in [file.name for file in canvas_create.files]
    assert len(canvas_create.files) == len(set([file.name for file in canvas_create.files]))
    print(canvas_create.files)
    

@composite
def canvas_rebuild_strategy(draw):
    files = draw(
        st.lists(
            st.builds(
                V2CanvasPredefinedFiles,
                name=st.sampled_from(list(V2CanvasPredefinedFileNames))
            )
        )
    )
    model = draw(
        st.builds(
            V3CanvasRebuild,
            files=st.just(files)
        )
    )
    assume(len(model.files))
    return model

@given(canvas_rebuild=canvas_rebuild_strategy())
def test_build_canvas_create_validate_files(canvas_rebuild):
    assert V2CanvasPredefinedFileNames.baseline_tags not in [file.name for file in
                                                             canvas_rebuild.files]
    assert len(canvas_rebuild.files) == len(
        set([file.name for file in canvas_rebuild.files])
        )
    