"""Property-based tests for pydantic.type_adapter.TypeAdapter using Hypothesis."""

import json
import math
from decimal import Decimal
from typing import Any, Dict, List, Optional, Union

import pytest
from hypothesis import assume, given, settings, strategies as st
from pydantic import TypeAdapter


# Strategy for generating JSON-compatible values
json_value = st.recursive(
    st.one_of(
        st.none(),
        st.booleans(),
        st.integers(min_value=-10**10, max_value=10**10),
        st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10),
        st.text(min_size=0, max_size=100),
    ),
    lambda children: st.one_of(
        st.lists(children, max_size=10),
        st.dictionaries(st.text(min_size=1, max_size=20), children, max_size=10)
    ),
    max_leaves=50
)


@given(json_value)
@settings(max_examples=500)
def test_json_round_trip_any_type(value):
    """Test that validate_json(dump_json(x)) == x for Any type."""
    ta = TypeAdapter(Any)
    
    # Dump to JSON and parse back
    json_bytes = ta.dump_json(value)
    recovered = ta.validate_json(json_bytes)
    
    # Check equality
    if isinstance(value, float) and math.isnan(value):
        assert math.isnan(recovered)
    else:
        assert recovered == value


@given(json_value)
@settings(max_examples=500)
def test_python_round_trip_any_type(value):
    """Test that validate_python(dump_python(x)) == x for Any type."""
    ta = TypeAdapter(Any)
    
    # First validate the input
    validated = ta.validate_python(value)
    
    # Dump to Python and parse back
    dumped = ta.dump_python(validated)
    recovered = ta.validate_python(dumped)
    
    # Check equality
    if isinstance(validated, float) and math.isnan(validated):
        assert math.isnan(recovered)
    else:
        assert recovered == validated


@given(st.lists(st.integers(min_value=-10000, max_value=10000), max_size=100))
@settings(max_examples=500)
def test_list_int_round_trip(value):
    """Test round-trip for List[int] type."""
    ta = TypeAdapter(List[int])
    
    # Test JSON round-trip
    json_bytes = ta.dump_json(value)
    recovered_json = ta.validate_json(json_bytes)
    assert recovered_json == value
    
    # Test Python round-trip
    dumped_python = ta.dump_python(value)
    recovered_python = ta.validate_python(dumped_python)
    assert recovered_python == value


@given(st.dictionaries(
    st.text(min_size=1, max_size=20),
    st.floats(allow_nan=False, allow_infinity=False, min_value=-1e6, max_value=1e6),
    max_size=50
))
@settings(max_examples=500)
def test_dict_str_float_round_trip(value):
    """Test round-trip for Dict[str, float] type."""
    ta = TypeAdapter(Dict[str, float])
    
    # Test JSON round-trip
    json_bytes = ta.dump_json(value)
    recovered_json = ta.validate_json(json_bytes)
    
    # Float comparison with tolerance
    assert len(recovered_json) == len(value)
    for key in value:
        assert key in recovered_json
        if not math.isclose(recovered_json[key], value[key], rel_tol=1e-9):
            # Check if it's a precision issue
            assert abs(recovered_json[key] - value[key]) < 1e-10


@given(json_value)
@settings(max_examples=500)
def test_validation_idempotence(value):
    """Test that validate_python(validate_python(x)) == validate_python(x)."""
    ta = TypeAdapter(Any)
    
    # First validation
    validated_once = ta.validate_python(value)
    
    # Second validation
    validated_twice = ta.validate_python(validated_once)
    
    # Should be equal
    if isinstance(validated_once, float) and math.isnan(validated_once):
        assert math.isnan(validated_twice)
    else:
        assert validated_twice == validated_once


@given(st.one_of(
    st.integers(min_value=-10**10, max_value=10**10),
    st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10),
    st.text(min_size=0, max_size=100),
    st.booleans(),
    st.none(),
))
@settings(max_examples=500)
def test_json_python_equivalence_simple_types(value):
    """Test that validate_json(json.dumps(x)) == validate_python(x) for simple types."""
    ta = TypeAdapter(Any)
    
    # Validate via Python
    python_validated = ta.validate_python(value)
    
    # Validate via JSON
    json_str = json.dumps(value)
    json_validated = ta.validate_json(json_str)
    
    # Should be equal
    if isinstance(value, float) and not math.isnan(value):
        # Handle floating point precision
        assert math.isclose(json_validated, python_validated, rel_tol=1e-9)
    elif isinstance(value, float) and math.isnan(value):
        # JSON doesn't support NaN
        pass  
    else:
        assert json_validated == python_validated


@given(st.one_of(st.none(), st.integers()))
@settings(max_examples=500)
def test_optional_int_round_trip(value):
    """Test round-trip for Optional[int] type."""
    ta = TypeAdapter(Optional[int])
    
    # Test JSON round-trip
    json_bytes = ta.dump_json(value)
    recovered_json = ta.validate_json(json_bytes)
    assert recovered_json == value
    
    # Test Python round-trip
    dumped_python = ta.dump_python(value)
    recovered_python = ta.validate_python(dumped_python)
    assert recovered_python == value


@given(st.one_of(st.integers(), st.text()))
@settings(max_examples=500)
def test_union_int_str_round_trip(value):
    """Test round-trip for Union[int, str] type."""
    ta = TypeAdapter(Union[int, str])
    
    # Test JSON round-trip
    json_bytes = ta.dump_json(value)
    recovered_json = ta.validate_json(json_bytes)
    assert recovered_json == value
    assert type(recovered_json) == type(value)
    
    # Test Python round-trip
    dumped_python = ta.dump_python(value)
    recovered_python = ta.validate_python(dumped_python)
    assert recovered_python == value
    assert type(recovered_python) == type(value)


@given(st.text(min_size=0, max_size=1000))
@settings(max_examples=500)
def test_string_special_chars_round_trip(value):
    """Test round-trip for strings with special characters."""
    ta = TypeAdapter(str)
    
    # Test JSON round-trip
    json_bytes = ta.dump_json(value)
    recovered_json = ta.validate_json(json_bytes)
    assert recovered_json == value
    
    # Test Python round-trip
    dumped_python = ta.dump_python(value)
    recovered_python = ta.validate_python(dumped_python)
    assert recovered_python == value


@given(st.lists(st.lists(st.integers(min_value=-100, max_value=100), max_size=10), max_size=10))
@settings(max_examples=500)
def test_nested_list_round_trip(value):
    """Test round-trip for nested lists."""
    ta = TypeAdapter(List[List[int]])
    
    # Test JSON round-trip
    json_bytes = ta.dump_json(value)
    recovered_json = ta.validate_json(json_bytes)
    assert recovered_json == value
    
    # Test Python round-trip
    dumped_python = ta.dump_python(value)
    recovered_python = ta.validate_python(dumped_python)
    assert recovered_python == value


@given(st.floats(allow_nan=False, allow_infinity=False))
@settings(max_examples=500)
def test_float_precision_round_trip(value):
    """Test round-trip for floats with focus on precision."""
    ta = TypeAdapter(float)
    
    # Test JSON round-trip
    json_bytes = ta.dump_json(value)
    recovered_json = ta.validate_json(json_bytes)
    
    # For floats, we need to be careful about precision
    if value == 0.0 or recovered_json == 0.0:
        assert abs(recovered_json - value) < 1e-15
    else:
        relative_error = abs((recovered_json - value) / value)
        assert relative_error < 1e-15 or recovered_json == value


@given(st.floats(allow_nan=False, allow_infinity=False))
@settings(max_examples=500)
def test_float_round_trip_mode(value):
    """Test that round_trip parameter preserves float precision."""
    ta = TypeAdapter(float)
    
    # Test with round_trip=True
    json_bytes_rt = ta.dump_json(value, round_trip=True)
    recovered_rt = ta.validate_json(json_bytes_rt)
    
    # Test with round_trip=False (default)
    json_bytes_normal = ta.dump_json(value, round_trip=False)
    recovered_normal = ta.validate_json(json_bytes_normal)
    
    # Both should preserve the value
    if value != 0.0:
        assert math.isclose(recovered_rt, value, rel_tol=1e-15)
        assert math.isclose(recovered_normal, value, rel_tol=1e-15)
    else:
        assert abs(recovered_rt - value) < 1e-15
        assert abs(recovered_normal - value) < 1e-15


# Test with Decimal for high precision
@given(st.decimals(allow_nan=False, allow_infinity=False, min_value=-10**10, max_value=10**10))
@settings(max_examples=500)
def test_decimal_round_trip(value):
    """Test round-trip for Decimal type."""
    ta = TypeAdapter(Decimal)
    
    # Test JSON round-trip
    json_bytes = ta.dump_json(value)
    recovered_json = ta.validate_json(json_bytes)
    assert recovered_json == value
    assert type(recovered_json) == Decimal
    
    # Test Python round-trip
    dumped_python = ta.dump_python(value)
    recovered_python = ta.validate_python(dumped_python)
    assert recovered_python == value
    assert type(recovered_python) == Decimal