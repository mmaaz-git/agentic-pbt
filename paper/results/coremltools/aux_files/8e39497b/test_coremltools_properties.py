import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/coremltools_env/lib/python3.13/site-packages')

import pytest
from hypothesis import given, strategies as st, settings, assume
import numpy as np
import coremltools.converters as ct
from coremltools.converters.mil.input_types import (
    Shape, RangeDim, EnumeratedShapes, ImageType, 
    TensorType, StateType, ColorLayout, _get_shaping_class
)


# Strategy for valid bounds
@st.composite
def range_dim_bounds(draw):
    """Generate valid lower and upper bounds for RangeDim"""
    lower = draw(st.integers(min_value=1, max_value=1000))
    # upper_bound can be -1 (unlimited) or >= lower_bound
    upper_strategy = st.one_of(
        st.just(-1),
        st.integers(min_value=lower, max_value=10000)
    )
    upper = draw(upper_strategy)
    return lower, upper


# Test 1: RangeDim default validation property
@given(
    lower_bound=st.integers(min_value=1, max_value=1000),
    upper_bound=st.one_of(st.just(-1), st.integers(min_value=1, max_value=10000)),
    default=st.one_of(st.none(), st.integers(min_value=-100, max_value=10100))
)
def test_rangedim_default_validation(lower_bound, upper_bound, default):
    """Test that RangeDim correctly validates default values"""
    # Skip invalid combinations where upper < lower (except -1)
    if upper_bound != -1 and upper_bound < lower_bound:
        assume(False)
    
    if default is not None:
        should_fail = False
        # Check if default is out of bounds
        if default < lower_bound:
            should_fail = True
        if upper_bound > 0 and default > upper_bound:
            should_fail = True
            
        if should_fail:
            with pytest.raises(ValueError):
                RangeDim(lower_bound=lower_bound, upper_bound=upper_bound, default=default)
        else:
            dim = RangeDim(lower_bound=lower_bound, upper_bound=upper_bound, default=default)
            assert dim.default == default
    else:
        # When default is None, it should use lower_bound
        dim = RangeDim(lower_bound=lower_bound, upper_bound=upper_bound, default=default)
        assert dim.default == lower_bound


# Test 2: Shape validation - dimensions cannot be None or -1
@given(st.lists(st.one_of(
    st.integers(min_value=1, max_value=1000),
    st.none(),
    st.just(-1)
), min_size=1, max_size=5))
def test_shape_dimension_validation(shape_list):
    """Test that Shape rejects None and -1 dimensions"""
    has_invalid = any(s is None or s == -1 for s in shape_list)
    
    if has_invalid:
        with pytest.raises(ValueError, match="Dimension cannot be None or -1"):
            Shape(shape_list)
    else:
        shape = Shape(shape_list)
        assert shape.shape == tuple(shape_list)


# Test 3: Shape with RangeDim uses correct defaults
@given(
    dims=st.lists(st.one_of(
        st.integers(min_value=1, max_value=100),
        st.builds(
            RangeDim,
            lower_bound=st.integers(min_value=1, max_value=50),
            upper_bound=st.integers(min_value=50, max_value=100),
            default=st.integers(min_value=1, max_value=100)
        )
    ), min_size=1, max_size=4)
)
def test_shape_rangedim_defaults(dims):
    """Test that Shape correctly uses RangeDim defaults"""
    # Filter to ensure RangeDim defaults are within bounds
    valid_dims = []
    for d in dims:
        if isinstance(d, RangeDim):
            if d.default < d.lower_bound or (d.upper_bound > 0 and d.default > d.upper_bound):
                continue  # Skip invalid RangeDims
        valid_dims.append(d)
    
    if not valid_dims:
        return  # Skip if no valid dims
    
    shape = Shape(valid_dims)
    
    # Check that default uses RangeDim.default for RangeDim, and the value itself for ints
    expected_default = []
    for d in valid_dims:
        if isinstance(d, RangeDim):
            expected_default.append(d.default)
        else:
            expected_default.append(d)
    
    assert shape.default == tuple(expected_default)


# Test 4: EnumeratedShapes must have at least 2 shapes
@given(st.lists(st.lists(st.integers(min_value=1, max_value=100), min_size=1, max_size=3)))
def test_enumerated_shapes_minimum_count(shapes_list):
    """Test that EnumeratedShapes requires at least 2 shapes"""
    if len(shapes_list) < 2:
        with pytest.raises(ValueError, match="len >= 2"):
            EnumeratedShapes(shapes_list)
    else:
        enum_shapes = EnumeratedShapes(shapes_list)
        assert len(enum_shapes.shapes) == len(shapes_list)


# Test 5: ImageType bias initialization based on color layout
@given(
    color_layout=st.sampled_from([ColorLayout.RGB, ColorLayout.BGR, 
                                   ColorLayout.GRAYSCALE, ColorLayout.GRAYSCALE_FLOAT16]),
    bias=st.one_of(st.none(), st.floats(min_value=-10, max_value=10),
                    st.lists(st.floats(min_value=-10, max_value=10), min_size=3, max_size=3))
)
def test_imagetype_bias_initialization(color_layout, bias):
    """Test ImageType bias initialization based on color layout"""
    img_type = ImageType(color_layout=color_layout, bias=bias)
    
    if bias is None:
        # Check default bias values
        if color_layout in (ColorLayout.GRAYSCALE, ColorLayout.GRAYSCALE_FLOAT16):
            assert img_type.bias == 0.0
        else:  # RGB or BGR
            assert img_type.bias == [0.0, 0.0, 0.0]
    else:
        assert img_type.bias == bias


# Test 6: ImageType grayscale_use_uint8 validation
@given(
    color_layout=st.sampled_from([ColorLayout.RGB, ColorLayout.BGR, 
                                   ColorLayout.GRAYSCALE, ColorLayout.GRAYSCALE_FLOAT16]),
    grayscale_use_uint8=st.booleans()
)
def test_imagetype_grayscale_uint8_validation(color_layout, grayscale_use_uint8):
    """Test that grayscale_use_uint8 can only be True for GRAYSCALE layout"""
    if grayscale_use_uint8 and color_layout != ColorLayout.GRAYSCALE:
        with pytest.raises(ValueError, match="grayscale_use_uint8.*can only be True.*GRAYSCALE"):
            ImageType(color_layout=color_layout, grayscale_use_uint8=grayscale_use_uint8)
    else:
        img_type = ImageType(color_layout=color_layout, grayscale_use_uint8=grayscale_use_uint8)
        if color_layout == ColorLayout.GRAYSCALE:
            assert img_type.grayscale_use_uint8 == grayscale_use_uint8
        else:
            assert img_type.grayscale_use_uint8 == False


# Test 7: _get_shaping_class round-trip property
@given(
    shape_data=st.lists(st.integers(min_value=1, max_value=100), min_size=1, max_size=4)
)
def test_get_shaping_class_shape_roundtrip(shape_data):
    """Test that _get_shaping_class returns the same Shape object when given a Shape"""
    original_shape = Shape(shape_data)
    result = _get_shaping_class(original_shape)
    assert result is original_shape  # Should be the exact same object


@given(
    shapes_data=st.lists(
        st.lists(st.integers(min_value=1, max_value=100), min_size=2, max_size=3),
        min_size=2, max_size=4
    )
)  
def test_get_shaping_class_enumshapes_roundtrip(shapes_data):
    """Test that _get_shaping_class returns the same EnumeratedShapes object"""
    original_enum = EnumeratedShapes(shapes_data)
    result = _get_shaping_class(original_enum)
    assert result is original_enum  # Should be the exact same object


# Test 8: StateType validation - wrapped type must not have name or default_value
@given(
    name=st.one_of(st.none(), st.text(min_size=1, max_size=10)),
    default_value=st.one_of(st.none(), st.floats())
)
def test_statetype_wrapped_validation(name, default_value):
    """Test that StateType validates its wrapped TensorType correctly"""
    wrapped = TensorType(
        name=name,
        shape=(2, 3),
        dtype=np.float32,
        default_value=default_value
    )
    
    should_fail = (name is not None or default_value is not None)
    
    if should_fail:
        with pytest.raises(ValueError):
            StateType(wrapped_type=wrapped, name="state")
    else:
        state = StateType(wrapped_type=wrapped, name="state")
        assert state.wrapped_type is wrapped
        assert not state.can_be_output()  # StateType cannot be output


if __name__ == "__main__":
    print("Running property-based tests for coremltools.converters...")
    pytest.main([__file__, "-v", "--tb=short"])