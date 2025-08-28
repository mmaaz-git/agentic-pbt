"""Property-based tests for troposphere.type_defs and encode_to_dict function."""

import math
from hypothesis import given, strategies as st, assume, settings
from troposphere import encode_to_dict
from typing import Any, Dict, List, Union


# Strategy for primitive types that should pass through unchanged
primitives = st.one_of(
    st.none(),
    st.booleans(),
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.text()
)

# Strategy for simple JSON-like data
json_like = st.recursive(
    primitives,
    lambda children: st.one_of(
        st.lists(children, max_size=5),
        st.dictionaries(st.text(min_size=1, max_size=10), children, max_size=5)
    ),
    max_leaves=20
)


class ObjectWithToDict:
    """Test class implementing to_dict protocol."""
    def __init__(self, data):
        self.data = data
    
    def to_dict(self):
        return self.data


class ObjectWithJSONrepr:
    """Test class implementing JSONrepr protocol."""
    def __init__(self, data):
        self.data = data
    
    def JSONrepr(self):
        return self.data


class ObjectWithBoth:
    """Test class implementing both protocols."""
    def __init__(self, to_dict_data, json_repr_data):
        self.to_dict_data = to_dict_data
        self.json_repr_data = json_repr_data
    
    def to_dict(self):
        return self.to_dict_data
    
    def JSONrepr(self):
        return self.json_repr_data


@given(primitives)
def test_primitive_pass_through(value):
    """Primitive types should pass through encode_to_dict unchanged."""
    result = encode_to_dict(value)
    assert result == value
    assert type(result) == type(value)


@given(st.tuples(st.integers(), st.text(), st.floats(allow_nan=False)))
def test_tuple_to_list_conversion(tup):
    """Tuples should be converted to lists but preserve order and elements."""
    result = encode_to_dict(tup)
    assert isinstance(result, list)
    assert len(result) == len(tup)
    assert result == list(tup)


@given(json_like)
def test_idempotence(data):
    """encode_to_dict should be idempotent: f(f(x)) == f(x)."""
    once = encode_to_dict(data)
    twice = encode_to_dict(once)
    assert once == twice


@given(st.dictionaries(st.text(min_size=1), primitives))
def test_dict_preservation(data):
    """Dictionaries should preserve their structure and keys."""
    result = encode_to_dict(data)
    assert isinstance(result, dict)
    assert set(result.keys()) == set(data.keys())
    for key in data:
        assert result[key] == data[key]


@given(st.lists(primitives, min_size=1))
def test_list_preservation(data):
    """Lists should preserve their order and elements."""
    result = encode_to_dict(data)
    assert isinstance(result, list)
    assert len(result) == len(data)
    assert result == data


@given(json_like)
def test_to_dict_protocol(data):
    """Objects with to_dict should have it called and result normalized."""
    obj = ObjectWithToDict(data)
    result = encode_to_dict(obj)
    # Result should be the normalized version of data
    assert result == encode_to_dict(data)


@given(json_like)
def test_jsonrepr_protocol(data):
    """Objects with JSONrepr should have it called and result normalized."""
    obj = ObjectWithJSONrepr(data)
    result = encode_to_dict(obj)
    # Result should be the normalized version of data
    assert result == encode_to_dict(data)


@given(json_like, json_like)
def test_protocol_priority(to_dict_data, json_repr_data):
    """When both to_dict and JSONrepr exist, to_dict takes priority."""
    assume(to_dict_data != json_repr_data)  # Make sure they're different
    obj = ObjectWithBoth(to_dict_data, json_repr_data)
    result = encode_to_dict(obj)
    # Should use to_dict, not JSONrepr
    assert result == encode_to_dict(to_dict_data)
    assert result != encode_to_dict(json_repr_data) if to_dict_data != json_repr_data else True


@given(st.lists(json_like, min_size=1, max_size=3))
def test_list_of_protocol_objects(data_list):
    """Lists of protocol objects should be properly normalized."""
    objects = [ObjectWithToDict(d) for d in data_list]
    result = encode_to_dict(objects)
    expected = [encode_to_dict(d) for d in data_list]
    assert result == expected


@given(st.dictionaries(st.text(min_size=1, max_size=5), json_like, min_size=1, max_size=3))
def test_dict_of_protocol_objects(data_dict):
    """Dicts with protocol object values should be properly normalized."""
    objects = {k: ObjectWithToDict(v) for k, v in data_dict.items()}
    result = encode_to_dict(objects)
    expected = {k: encode_to_dict(v) for k, v in data_dict.items()}
    assert result == expected


class RecursiveToDict:
    """Test class with recursive to_dict implementation."""
    def __init__(self, depth, value):
        self.depth = depth
        self.value = value
    
    def to_dict(self):
        if self.depth > 0:
            return {
                'depth': self.depth,
                'value': self.value,
                'child': RecursiveToDict(self.depth - 1, self.value)
            }
        return {'depth': 0, 'value': self.value}


@given(st.integers(min_value=0, max_value=10), primitives)
def test_recursive_normalization(depth, value):
    """Recursive structures should be fully normalized to base types."""
    obj = RecursiveToDict(depth, value)
    result = encode_to_dict(obj)
    
    # Check it's fully normalized (no objects remain)
    def check_normalized(data):
        if isinstance(data, dict):
            for v in data.values():
                check_normalized(v)
        elif isinstance(data, list):
            for item in data:
                check_normalized(item)
        else:
            # Should be a primitive type
            assert not hasattr(data, 'to_dict')
            assert not hasattr(data, 'JSONrepr')
    
    check_normalized(result)
    
    # Check depth is preserved
    current = result
    for i in range(depth, 0, -1):
        assert current['depth'] == i
        assert current['value'] == value
        if i > 0:
            current = current.get('child', {})


@given(st.lists(st.tuples(st.integers(), st.text()), min_size=1, max_size=5))
def test_nested_tuple_conversion(data):
    """Nested tuples should all be converted to lists."""
    result = encode_to_dict(data)
    assert isinstance(result, list)
    for item in result:
        assert isinstance(item, list)
        assert len(item) == 2


class CyclicToDict:
    """Test class that could create cycles if not careful."""
    def __init__(self):
        self.ref = self
    
    def to_dict(self):
        # Return a simple dict to avoid actual cycles
        return {'type': 'cyclic'}


@given(st.integers(min_value=1, max_value=5))
def test_no_infinite_recursion(n):
    """encode_to_dict should handle potentially cyclic structures."""
    objects = [CyclicToDict() for _ in range(n)]
    result = encode_to_dict(objects)
    assert result == [{'type': 'cyclic'} for _ in range(n)]