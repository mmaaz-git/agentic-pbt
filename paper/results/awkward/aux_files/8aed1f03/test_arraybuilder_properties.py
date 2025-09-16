"""Property-based tests for awkward.ArrayBuilder"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/awkward_env/lib/python3.13/site-packages')

import awkward as ak
from hypothesis import given, strategies as st, assume, settings
import pytest
import math


# Test 1: Length monotonicity - operations should never decrease length
@given(
    values=st.lists(
        st.one_of(
            st.none(),
            st.booleans(),
            st.integers(min_value=-1e10, max_value=1e10),
            st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10),
            st.text(min_size=0, max_size=100),
        ),
        min_size=0,
        max_size=50
    )
)
def test_length_monotonicity(values):
    """Length should never decrease when appending values"""
    builder = ak.ArrayBuilder()
    prev_len = len(builder)
    
    for value in values:
        builder.append(value)
        current_len = len(builder)
        assert current_len >= prev_len, f"Length decreased from {prev_len} to {current_len}"
        prev_len = current_len


# Test 2: Round-trip preservation for simple values
@given(
    values=st.lists(
        st.one_of(
            st.none(),
            st.booleans(),
            st.integers(min_value=-1e10, max_value=1e10),
            st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10),
        ),
        min_size=0,
        max_size=20
    )
)
def test_roundtrip_simple_values(values):
    """Building an array and converting to list should preserve simple values"""
    builder = ak.ArrayBuilder()
    
    for value in values:
        builder.append(value)
    
    result = builder.snapshot().to_list()
    
    # Handle float comparison
    for i, (expected, actual) in enumerate(zip(values, result)):
        if isinstance(expected, float) and isinstance(actual, float):
            if math.isnan(expected):
                assert math.isnan(actual)
            else:
                assert math.isclose(expected, actual, rel_tol=1e-9)
        else:
            assert expected == actual, f"Mismatch at index {i}: {expected} != {actual}"


# Test 3: Snapshot consistency - multiple snapshots should be equivalent
@given(
    values=st.lists(
        st.one_of(
            st.none(),
            st.booleans(),
            st.integers(min_value=-1e10, max_value=1e10),
            st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10),
        ),
        min_size=1,
        max_size=20
    )
)
def test_snapshot_consistency(values):
    """Multiple snapshots without modifications should produce equivalent arrays"""
    builder = ak.ArrayBuilder()
    
    for value in values:
        builder.append(value)
    
    snapshot1 = builder.snapshot()
    snapshot2 = builder.snapshot()
    
    assert snapshot1.to_list() == snapshot2.to_list()
    assert len(snapshot1) == len(snapshot2)
    assert str(snapshot1.type) == str(snapshot2.type)


# Test 4: Nested list structure preservation
@given(
    lists_data=st.lists(
        st.lists(
            st.integers(min_value=-1000, max_value=1000),
            min_size=0,
            max_size=5
        ),
        min_size=0,
        max_size=10
    )
)
def test_nested_lists_roundtrip(lists_data):
    """Nested lists should be preserved through build/snapshot/to_list cycle"""
    builder = ak.ArrayBuilder()
    
    for inner_list in lists_data:
        builder.begin_list()
        for value in inner_list:
            builder.integer(value)
        builder.end_list()
    
    result = builder.snapshot().to_list()
    assert result == lists_data


# Test 5: Record field preservation
@given(
    records=st.lists(
        st.dictionaries(
            keys=st.sampled_from(["x", "y", "z", "value", "id"]),
            values=st.one_of(
                st.integers(min_value=-1000, max_value=1000),
                st.floats(allow_nan=False, allow_infinity=False, min_value=-100, max_value=100),
            ),
            min_size=1,
            max_size=3
        ),
        min_size=0,
        max_size=10
    )
)
def test_record_fields_preservation(records):
    """Record fields should be preserved correctly"""
    builder = ak.ArrayBuilder()
    
    for record in records:
        builder.begin_record()
        for key, value in record.items():
            if isinstance(value, int):
                builder.field(key).integer(value)
            else:
                builder.field(key).real(value)
        builder.end_record()
    
    result = builder.snapshot().to_list()
    
    # Check structure is preserved
    assert len(result) == len(records)
    for expected, actual in zip(records, result):
        assert set(expected.keys()) == set(actual.keys())
        for key in expected.keys():
            if isinstance(expected[key], float) and isinstance(actual[key], float):
                assert math.isclose(expected[key], actual[key], rel_tol=1e-9)
            else:
                assert expected[key] == actual[key]


# Test 6: Unbalanced begin/end operations should raise errors
def test_unbalanced_list_operations():
    """Unbalanced begin_list without end_list should raise an error"""
    builder = ak.ArrayBuilder()
    builder.begin_list()
    builder.integer(1)
    # Missing end_list()
    
    # Trying to snapshot with unbalanced list should raise an error
    with pytest.raises(Exception):
        builder.snapshot()


def test_unbalanced_record_operations():
    """Unbalanced begin_record without end_record should raise an error"""
    builder = ak.ArrayBuilder()
    builder.begin_record()
    builder.field("x").integer(1)
    # Missing end_record()
    
    # Trying to snapshot with unbalanced record should raise an error
    with pytest.raises(Exception):
        builder.snapshot()


# Test 7: Mixed types handling
@given(
    operations=st.lists(
        st.one_of(
            st.tuples(st.just("integer"), st.integers(min_value=-1000, max_value=1000)),
            st.tuples(st.just("real"), st.floats(allow_nan=False, allow_infinity=False, min_value=-100, max_value=100)),
            st.tuples(st.just("null"), st.none()),
            st.tuples(st.just("string"), st.text(min_size=0, max_size=20)),
        ),
        min_size=1,
        max_size=20
    )
)
def test_mixed_types_in_list(operations):
    """Mixed types in a list should be handled correctly"""
    builder = ak.ArrayBuilder()
    builder.begin_list()
    
    expected = []
    for op_type, value in operations:
        if op_type == "integer":
            builder.integer(value)
            expected.append(value)
        elif op_type == "real":
            builder.real(value)
            expected.append(value)
        elif op_type == "null":
            builder.null()
            expected.append(None)
        elif op_type == "string":
            builder.string(value)
            expected.append(value)
    
    builder.end_list()
    result = builder.snapshot().to_list()
    
    assert len(result) == 1
    assert len(result[0]) == len(expected)
    
    for exp, act in zip(expected, result[0]):
        if isinstance(exp, float) and isinstance(act, float):
            assert math.isclose(exp, act, rel_tol=1e-9)
        else:
            assert exp == act


# Test 8: Empty builder behavior
def test_empty_builder():
    """Empty builder should produce empty array"""
    builder = ak.ArrayBuilder()
    snapshot = builder.snapshot()
    
    assert len(snapshot) == 0
    assert snapshot.to_list() == []


# Test 9: Extend method functionality
@given(
    initial=st.lists(st.integers(min_value=-100, max_value=100), min_size=0, max_size=10),
    extension=st.lists(st.integers(min_value=-100, max_value=100), min_size=0, max_size=10)
)
def test_extend_method(initial, extension):
    """Extend method should append all values from iterable"""
    builder = ak.ArrayBuilder()
    
    # Add initial values one by one
    for value in initial:
        builder.append(value)
    
    # Extend with additional values
    builder.extend(extension)
    
    result = builder.snapshot().to_list()
    expected = initial + extension
    
    assert result == expected


if __name__ == "__main__":
    # Run the tests
    print("Running property-based tests for awkward.ArrayBuilder...")
    pytest.main([__file__, "-v"])