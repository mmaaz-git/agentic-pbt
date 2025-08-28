"""Additional edge case tests for pydantic.type_adapter.TypeAdapter."""

import json
from typing import Any, Dict, List, Tuple, Set, FrozenSet
from collections import deque
from datetime import datetime, date, time, timedelta
from uuid import UUID
import uuid

import pytest
from hypothesis import assume, given, settings, strategies as st
from pydantic import TypeAdapter


# Test with tuples (immutable sequences)
@given(st.tuples(st.integers(), st.text(), st.floats(allow_nan=False, allow_infinity=False)))
@settings(max_examples=500)
def test_tuple_round_trip(value):
    """Test round-trip for Tuple type."""
    ta = TypeAdapter(Tuple[int, str, float])
    
    # Test JSON round-trip - tuples become lists in JSON
    json_bytes = ta.dump_json(value)
    recovered_json = ta.validate_json(json_bytes)
    assert recovered_json == value
    assert isinstance(recovered_json, tuple)
    
    # Test Python round-trip
    dumped_python = ta.dump_python(value)
    recovered_python = ta.validate_python(dumped_python)
    assert recovered_python == value
    assert isinstance(recovered_python, tuple)


# Test with sets (which don't have direct JSON representation)
@given(st.sets(st.integers(min_value=-1000, max_value=1000), max_size=20))
@settings(max_examples=500)
def test_set_round_trip(value):
    """Test round-trip for Set type."""
    ta = TypeAdapter(Set[int])
    
    # Test JSON round-trip - sets become lists in JSON
    json_bytes = ta.dump_json(value)
    recovered_json = ta.validate_json(json_bytes)
    assert recovered_json == value
    assert isinstance(recovered_json, set)
    
    # Test Python round-trip
    dumped_python = ta.dump_python(value)
    recovered_python = ta.validate_python(dumped_python)
    assert recovered_python == value
    assert isinstance(recovered_python, set)


# Test with frozensets
@given(st.frozensets(st.text(min_size=1, max_size=10), max_size=10))
@settings(max_examples=500)
def test_frozenset_round_trip(value):
    """Test round-trip for FrozenSet type."""
    ta = TypeAdapter(FrozenSet[str])
    
    # Test JSON round-trip
    json_bytes = ta.dump_json(value)
    recovered_json = ta.validate_json(json_bytes)
    assert recovered_json == value
    assert isinstance(recovered_json, frozenset)
    
    # Test Python round-trip
    dumped_python = ta.dump_python(value)
    recovered_python = ta.validate_python(dumped_python)
    assert recovered_python == value
    assert isinstance(recovered_python, frozenset)


# Test with bytes
@given(st.binary(max_size=1000))
@settings(max_examples=500)
def test_bytes_round_trip(value):
    """Test round-trip for bytes type."""
    ta = TypeAdapter(bytes)
    
    # Test JSON round-trip - bytes are base64 encoded in JSON
    json_bytes = ta.dump_json(value)
    recovered_json = ta.validate_json(json_bytes)
    assert recovered_json == value
    assert isinstance(recovered_json, bytes)
    
    # Test Python round-trip
    dumped_python = ta.dump_python(value)
    recovered_python = ta.validate_python(dumped_python)
    assert recovered_python == value
    assert isinstance(recovered_python, bytes)


# Test with datetime types
@given(st.datetimes(min_value=datetime(1900, 1, 1), max_value=datetime(2100, 1, 1)))
@settings(max_examples=500)
def test_datetime_round_trip(value):
    """Test round-trip for datetime type."""
    ta = TypeAdapter(datetime)
    
    # Test JSON round-trip
    json_bytes = ta.dump_json(value)
    recovered_json = ta.validate_json(json_bytes)
    assert recovered_json == value
    assert isinstance(recovered_json, datetime)
    
    # Test Python round-trip
    dumped_python = ta.dump_python(value)
    recovered_python = ta.validate_python(dumped_python)
    assert recovered_python == value
    assert isinstance(recovered_python, datetime)


@given(st.dates(min_value=date(1900, 1, 1), max_value=date(2100, 1, 1)))
@settings(max_examples=500)
def test_date_round_trip(value):
    """Test round-trip for date type."""
    ta = TypeAdapter(date)
    
    # Test JSON round-trip
    json_bytes = ta.dump_json(value)
    recovered_json = ta.validate_json(json_bytes)
    assert recovered_json == value
    assert isinstance(recovered_json, date)
    
    # Test Python round-trip
    dumped_python = ta.dump_python(value)
    recovered_python = ta.validate_python(dumped_python)
    assert recovered_python == value
    assert isinstance(recovered_python, date)


@given(st.times())
@settings(max_examples=500)
def test_time_round_trip(value):
    """Test round-trip for time type."""
    ta = TypeAdapter(time)
    
    # Test JSON round-trip
    json_bytes = ta.dump_json(value)
    recovered_json = ta.validate_json(json_bytes)
    assert recovered_json == value
    assert isinstance(recovered_json, time)
    
    # Test Python round-trip
    dumped_python = ta.dump_python(value)
    recovered_python = ta.validate_python(dumped_python)
    assert recovered_python == value
    assert isinstance(recovered_python, time)


@given(st.timedeltas(min_value=timedelta(days=-999), max_value=timedelta(days=999)))
@settings(max_examples=500)
def test_timedelta_round_trip(value):
    """Test round-trip for timedelta type."""
    ta = TypeAdapter(timedelta)
    
    # Test JSON round-trip
    json_bytes = ta.dump_json(value)
    recovered_json = ta.validate_json(json_bytes)
    assert recovered_json == value
    assert isinstance(recovered_json, timedelta)
    
    # Test Python round-trip
    dumped_python = ta.dump_python(value)
    recovered_python = ta.validate_python(dumped_python)
    assert recovered_python == value
    assert isinstance(recovered_python, timedelta)


# Test with UUID
@given(st.uuids())
@settings(max_examples=500)
def test_uuid_round_trip(value):
    """Test round-trip for UUID type."""
    ta = TypeAdapter(UUID)
    
    # Test JSON round-trip
    json_bytes = ta.dump_json(value)
    recovered_json = ta.validate_json(json_bytes)
    assert recovered_json == value
    assert isinstance(recovered_json, UUID)
    
    # Test Python round-trip
    dumped_python = ta.dump_python(value)
    recovered_python = ta.validate_python(dumped_python)
    assert recovered_python == value
    assert isinstance(recovered_python, UUID)


# Test deeply nested structures
@given(st.recursive(
    st.integers(min_value=-100, max_value=100),
    lambda children: st.lists(children, min_size=1, max_size=3),
    max_leaves=30
))
@settings(max_examples=200)
def test_deeply_nested_lists(value):
    """Test round-trip for deeply nested list structures."""
    ta = TypeAdapter(Any)
    
    # Test JSON round-trip
    json_bytes = ta.dump_json(value)
    recovered_json = ta.validate_json(json_bytes)
    assert recovered_json == value
    
    # Test Python round-trip
    dumped_python = ta.dump_python(value)
    recovered_python = ta.validate_python(dumped_python)
    assert recovered_python == value


# Test with complex nested dictionary
@given(st.recursive(
    st.one_of(st.integers(), st.text(max_size=10), st.none()),
    lambda children: st.dictionaries(
        st.text(min_size=1, max_size=5),
        children,
        max_size=3
    ),
    max_leaves=20
))
@settings(max_examples=200)
def test_deeply_nested_dicts(value):
    """Test round-trip for deeply nested dictionary structures."""
    ta = TypeAdapter(Any)
    
    # Test JSON round-trip
    json_bytes = ta.dump_json(value)
    recovered_json = ta.validate_json(json_bytes)
    assert recovered_json == value
    
    # Test Python round-trip
    dumped_python = ta.dump_python(value)
    recovered_python = ta.validate_python(dumped_python)
    assert recovered_python == value


# Test empty collections
@given(st.just([]))
def test_empty_list(value):
    """Test empty list round-trip."""
    ta = TypeAdapter(List[Any])
    json_bytes = ta.dump_json(value)
    assert ta.validate_json(json_bytes) == value


@given(st.just({}))
def test_empty_dict(value):
    """Test empty dict round-trip."""
    ta = TypeAdapter(Dict[str, Any])
    json_bytes = ta.dump_json(value)
    assert ta.validate_json(json_bytes) == value


@given(st.just(set()))
def test_empty_set(value):
    """Test empty set round-trip."""
    ta = TypeAdapter(Set[Any])
    json_bytes = ta.dump_json(value)
    recovered = ta.validate_json(json_bytes)
    assert recovered == value
    assert isinstance(recovered, set)


# Test with very large numbers
@given(st.integers(min_value=2**53, max_value=2**63-1))
@settings(max_examples=500)
def test_large_integers_round_trip(value):
    """Test round-trip for large integers that might exceed JavaScript's safe integer range."""
    ta = TypeAdapter(int)
    
    # Test JSON round-trip
    json_bytes = ta.dump_json(value)
    recovered_json = ta.validate_json(json_bytes)
    assert recovered_json == value
    assert isinstance(recovered_json, int)
    
    # Test Python round-trip
    dumped_python = ta.dump_python(value)
    recovered_python = ta.validate_python(dumped_python)
    assert recovered_python == value