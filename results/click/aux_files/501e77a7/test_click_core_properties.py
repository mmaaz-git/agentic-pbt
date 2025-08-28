import sys
import math
from hypothesis import given, strategies as st, settings, assume
import click.core
from click.utils import make_str
from click.core import batch, iter_params_for_processing, Parameter, Option, Argument


# Test 1: batch function properties
@given(
    st.lists(st.integers(), min_size=0, max_size=100),
    st.integers(min_value=1, max_value=20)
)
def test_batch_preserves_elements(items, batch_size):
    """All elements from input should appear in batched output"""
    batched = batch(items, batch_size)
    flattened = [item for batch_tuple in batched for item in batch_tuple]
    
    # Property: All original elements should be present
    assert sorted(items) == sorted(flattened), f"Elements lost or added during batching"


@given(
    st.lists(st.integers(), min_size=0, max_size=100),
    st.integers(min_value=1, max_value=20)
)
def test_batch_maintains_order(items, batch_size):
    """Elements should maintain their relative order after batching"""
    batched = batch(items, batch_size)
    flattened = [item for batch_tuple in batched for item in batch_tuple]
    
    # Property: Order should be preserved
    assert items[:len(flattened)] == flattened, f"Order not preserved during batching"


@given(
    st.lists(st.integers(), min_size=0, max_size=100),
    st.integers(min_value=1, max_value=20)
)
def test_batch_size_consistency(items, batch_size):
    """All batches except the last should have exactly batch_size elements"""
    batched = batch(items, batch_size)
    
    if len(batched) > 0:
        # All batches except possibly the last should have batch_size elements
        for i, batch_tuple in enumerate(batched[:-1]):
            assert len(batch_tuple) == batch_size, f"Batch {i} has wrong size: {len(batch_tuple)} != {batch_size}"
        
        # Last batch should have at most batch_size elements
        if batched:
            assert len(batched[-1]) <= batch_size, f"Last batch too large: {len(batched[-1])} > {batch_size}"


@given(
    st.lists(st.integers(), min_size=0, max_size=100),
    st.integers(min_value=1, max_value=20)
)
def test_batch_count_property(items, batch_size):
    """Number of batches should match mathematical expectation"""
    batched = batch(items, batch_size)
    expected_batch_count = math.ceil(len(items) / batch_size) if items else 0
    
    # Property: batch count should match ceiling division
    assert len(batched) == expected_batch_count, f"Wrong number of batches: {len(batched)} != {expected_batch_count}"


# Test 2: make_str round-trip properties
@given(st.text())
def test_make_str_idempotent(text):
    """make_str should be idempotent for strings"""
    result1 = make_str(text)
    result2 = make_str(result1)
    assert result1 == result2, "make_str not idempotent for strings"


@given(st.binary(min_size=0, max_size=1000))
def test_make_str_bytes_roundtrip(data):
    """Converting bytes to string and back should preserve or replace invalid chars"""
    try:
        # Try to decode with filesystem encoding
        expected = data.decode(sys.getfilesystemencoding())
        result = make_str(data)
        assert result == expected
    except UnicodeError:
        # Should fall back to UTF-8 with replace
        result = make_str(data)
        # Result should be a valid string (no exception)
        assert isinstance(result, str)
        # Should use replace error handler - no exceptions
        assert result == data.decode("utf-8", "replace")


@given(st.integers())
def test_make_str_integers(num):
    """make_str should convert integers to their string representation"""
    result = make_str(num)
    assert result == str(num)
    assert isinstance(result, str)


@given(st.floats(allow_nan=True, allow_infinity=True))
def test_make_str_floats(num):
    """make_str should convert floats to their string representation"""
    result = make_str(num)
    assert result == str(num)
    assert isinstance(result, str)


# Test 3: iter_params_for_processing properties
def create_parameter(name, is_eager=False):
    """Helper to create test parameters"""
    param = Parameter([f"--{name}"])
    param.is_eager = is_eager
    param.name = name
    return param


@given(
    st.lists(st.text(min_size=1, max_size=10), min_size=1, max_size=10, unique=True)
)
def test_iter_params_preserves_all_params(param_names):
    """All declaration parameters should be in the result"""
    params = [create_parameter(name) for name in param_names]
    
    # Test with empty invocation order
    result = iter_params_for_processing([], params)
    assert set(result) == set(params), "Not all parameters preserved"
    assert len(result) == len(params), "Parameter count changed"


@given(
    st.lists(st.text(min_size=1, max_size=10), min_size=2, max_size=10, unique=True)
)
def test_iter_params_invocation_order_respected(param_names):
    """Parameters in invocation order should appear before others"""
    params = [create_parameter(name) for name in param_names]
    
    # Use first half as invocation order
    mid = len(params) // 2
    invocation_order = params[:mid]
    
    result = iter_params_for_processing(invocation_order, params)
    
    # Check that invoked params appear in the same relative order
    result_indices = {p: i for i, p in enumerate(result)}
    
    for i in range(len(invocation_order) - 1):
        param1 = invocation_order[i]
        param2 = invocation_order[i + 1]
        assert result_indices[param1] < result_indices[param2], \
            "Invocation order not preserved"


@given(
    st.lists(st.text(min_size=1, max_size=10), min_size=2, max_size=10, unique=True),
    st.lists(st.booleans(), min_size=2, max_size=10)
)
def test_iter_params_eager_params_first(param_names, eager_flags):
    """Eager parameters should be processed before non-eager ones"""
    # Ensure we have same number of flags as names
    eager_flags = eager_flags[:len(param_names)]
    while len(eager_flags) < len(param_names):
        eager_flags.append(False)
    
    params = [create_parameter(name, is_eager=eager) 
              for name, eager in zip(param_names, eager_flags)]
    
    # Test with empty invocation order
    result = iter_params_for_processing([], params)
    
    # Find first non-eager and last eager param
    eager_indices = [i for i, p in enumerate(result) if p.is_eager]
    non_eager_indices = [i for i, p in enumerate(result) if not p.is_eager]
    
    if eager_indices and non_eager_indices:
        # All eager params should come before non-eager params
        assert max(eager_indices) < min(non_eager_indices), \
            "Eager parameters not processed first"


# Test 4: Batch function with various input types
@given(st.text())
def test_batch_with_strings(text):
    """Batch should work with string iterables (chars)"""
    if text:
        batch_size = min(3, len(text))
        batched = batch(text, batch_size)
        flattened = ''.join(''.join(b) for b in batched)
        # Should preserve all characters
        assert text[:len(flattened)] == flattened


@given(
    st.lists(st.tuples(st.integers(), st.text()), min_size=0, max_size=50),
    st.integers(min_value=1, max_value=10)
)
def test_batch_with_tuples(items, batch_size):
    """Batch should work with any iterable type"""
    batched = batch(items, batch_size)
    flattened = [item for batch_tuple in batched for item in batch_tuple]
    assert items[:len(flattened)] == flattened


# Edge case: batch with batch_size of 1
@given(st.lists(st.integers(), min_size=0, max_size=100))
def test_batch_size_one(items):
    """Batch with size 1 should create single-element tuples"""
    batched = batch(items, 1)
    
    # Each batch should have exactly 1 element
    for b in batched:
        assert len(b) == 1
    
    # Should preserve all elements
    flattened = [item for batch_tuple in batched for item in batch_tuple]
    assert items == flattened


if __name__ == "__main__":
    # Run tests with pytest
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])