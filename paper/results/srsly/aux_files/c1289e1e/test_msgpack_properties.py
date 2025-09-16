#!/usr/bin/env python3
"""Property-based tests for srsly.msgpack using Hypothesis."""

import sys
import os
import math
import numpy as np
from hypothesis import given, strategies as st, settings, assume

# Add the site-packages to path
sys.path.insert(0, '/root/hypothesis-llm/envs/srsly_env/lib/python3.13/site-packages')

from srsly._msgpack_api import msgpack_dumps, msgpack_loads


# Strategy for valid msgpack data types
def msgpack_serializable():
    """Generate data that should be serializable by msgpack."""
    return st.recursive(
        st.one_of(
            st.none(),
            st.booleans(),
            st.integers(min_value=-(2**63), max_value=2**63-1),
            st.floats(allow_nan=False, allow_infinity=False),
            st.text(),
            st.binary(max_size=1000),
        ),
        lambda children: st.one_of(
            st.lists(children, max_size=10),
            st.dictionaries(
                st.one_of(st.text(max_size=50), st.binary(max_size=50)),
                children,
                max_size=10
            ),
        ),
        max_leaves=50
    )


@given(msgpack_serializable())
@settings(max_examples=1000)
def test_msgpack_round_trip_basic(data):
    """Test that basic data types survive msgpack serialization round-trip."""
    packed = msgpack_dumps(data)
    unpacked = msgpack_loads(packed)
    
    # Handle float comparison specially
    def compare(a, b):
        if isinstance(a, float) and isinstance(b, float):
            if math.isnan(a) and math.isnan(b):
                return True
            return math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-9)
        elif isinstance(a, dict) and isinstance(b, dict):
            if set(a.keys()) != set(b.keys()):
                return False
            return all(compare(a[k], b[k]) for k in a.keys())
        elif isinstance(a, list) and isinstance(b, list):
            if len(a) != len(b):
                return False
            return all(compare(x, y) for x, y in zip(a, b))
        else:
            return a == b
    
    assert compare(data, unpacked)


@given(
    st.one_of(
        st.tuples(st.integers(1, 100)),
        st.tuples(st.integers(1, 50), st.integers(1, 50)),
        st.tuples(st.integers(1, 20), st.integers(1, 20), st.integers(1, 20)),
    ),
    st.sampled_from([np.float32, np.float64, np.int32, np.int64, np.uint8, np.uint16, np.uint32, np.uint64])
)
@settings(max_examples=500)
def test_numpy_array_round_trip(shape, dtype):
    """Test that numpy arrays survive msgpack serialization with shape and dtype preserved."""
    # Generate array data based on dtype
    if dtype in [np.float32, np.float64]:
        data = np.random.randn(*shape).astype(dtype)
    else:
        info = np.iinfo(dtype)
        data = np.random.randint(info.min, info.max if info.max < 2**31 else 2**31-1, size=shape, dtype=dtype)
    
    # Wrap in dict as msgpack expects dict/list at top level
    original = {"array": data}
    packed = msgpack_dumps(original)
    unpacked = msgpack_loads(packed)
    
    assert "array" in unpacked
    result = unpacked["array"]
    assert isinstance(result, np.ndarray)
    assert result.shape == data.shape
    assert result.dtype == data.dtype
    assert np.array_equal(result, data)


@given(st.complex_numbers(allow_nan=False, allow_infinity=False))
@settings(max_examples=500)
def test_complex_number_round_trip(c):
    """Test that complex numbers survive msgpack serialization."""
    # Complex numbers are encoded as special dicts with __repr__
    original = {"complex": c}
    packed = msgpack_dumps(original)
    unpacked = msgpack_loads(packed)
    
    assert "complex" in unpacked
    result = unpacked["complex"]
    assert isinstance(result, complex)
    assert math.isclose(result.real, c.real, rel_tol=1e-9, abs_tol=1e-9)
    assert math.isclose(result.imag, c.imag, rel_tol=1e-9, abs_tol=1e-9)


@given(st.lists(st.integers(), min_size=1, max_size=10))
@settings(max_examples=500)  
def test_use_list_parameter(data):
    """Test that use_list parameter controls list vs tuple deserialization."""
    # When serializing a list
    original = {"data": data}
    packed = msgpack_dumps(original)
    
    # With use_list=True (default), we get lists
    with_list = msgpack_loads(packed, use_list=True)
    assert isinstance(with_list["data"], list)
    assert with_list["data"] == data
    
    # With use_list=False, we get tuples
    with_tuple = msgpack_loads(packed, use_list=False)
    assert isinstance(with_tuple["data"], tuple)
    assert list(with_tuple["data"]) == data


@given(st.lists(st.floats(allow_nan=False, allow_infinity=False, min_value=-1e6, max_value=1e6)))
@settings(max_examples=500)
def test_numpy_scalar_round_trip(values):
    """Test that numpy scalar types survive msgpack serialization."""
    assume(len(values) > 0)
    
    # Create numpy scalars of different types
    scalars = {
        "float32": np.float32(values[0]) if values else np.float32(0),
        "float64": np.float64(values[0]) if values else np.float64(0),
    }
    
    if values:
        int_val = int(values[0]) if abs(values[0]) < 2**31 else 0
        scalars.update({
            "int32": np.int32(int_val),
            "int64": np.int64(int_val),
        })
    
    packed = msgpack_dumps(scalars)
    unpacked = msgpack_loads(packed)
    
    for key in scalars:
        assert key in unpacked
        # Numpy scalars are unpacked as regular Python types
        if "float" in key:
            assert isinstance(unpacked[key], (float, np.floating))
            assert math.isclose(float(unpacked[key]), float(scalars[key]), rel_tol=1e-6)
        else:
            assert isinstance(unpacked[key], (int, np.integer))
            assert int(unpacked[key]) == int(scalars[key])


@given(st.dictionaries(st.binary(min_size=1, max_size=100), st.integers()))
@settings(max_examples=500)
def test_binary_keys_round_trip(data):
    """Test that dictionaries with binary keys survive round-trip."""
    packed = msgpack_dumps(data)
    unpacked = msgpack_loads(packed)
    
    # Binary keys should be preserved
    assert set(data.keys()) == set(unpacked.keys())
    for key in data:
        assert unpacked[key] == data[key]


@given(st.lists(st.integers(min_value=0, max_value=255), min_size=1, max_size=1000))
@settings(max_examples=500)
def test_bytes_round_trip(byte_values):
    """Test that bytes data survives round-trip."""
    data = bytes(byte_values)
    original = {"bytes": data}
    
    packed = msgpack_dumps(original)
    unpacked = msgpack_loads(packed)
    
    assert "bytes" in unpacked
    assert isinstance(unpacked["bytes"], bytes)
    assert unpacked["bytes"] == data


@given(
    st.lists(st.integers(1, 10), min_size=2, max_size=4),
    st.sampled_from(['<', '>', '=', '|'])
)
@settings(max_examples=200)
def test_numpy_structured_array_round_trip(shape, byteorder):
    """Test that numpy structured arrays with complex dtypes survive round-trip."""
    # Create a structured dtype
    dt = np.dtype([
        ('x', f'{byteorder}f4'),
        ('y', f'{byteorder}f4'),
        ('z', f'{byteorder}i4')
    ])
    
    # Create structured array
    arr = np.zeros(shape, dtype=dt)
    arr['x'] = np.random.randn(*shape)
    arr['y'] = np.random.randn(*shape)
    arr['z'] = np.random.randint(-100, 100, shape)
    
    original = {"structured": arr}
    packed = msgpack_dumps(original)
    unpacked = msgpack_loads(packed)
    
    assert "structured" in unpacked
    result = unpacked["structured"]
    assert isinstance(result, np.ndarray)
    assert result.dtype == arr.dtype
    assert result.shape == arr.shape
    assert np.array_equal(result, arr)


if __name__ == "__main__":
    # Run the tests
    print("Running property-based tests for srsly.msgpack...")
    import pytest
    pytest.main([__file__, "-v"])