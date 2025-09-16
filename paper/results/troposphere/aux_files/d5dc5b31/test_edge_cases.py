"""Additional edge case tests for encode_to_dict."""

from hypothesis import given, strategies as st, settings
from troposphere import encode_to_dict
import sys
import math


# Test with large nested structures
@given(st.integers(min_value=100, max_value=500))
@settings(max_examples=10)
def test_deep_nesting(depth):
    """Test with deeply nested structures."""
    # Create deeply nested dict
    nested = {'value': 0}
    for i in range(depth):
        nested = {'level': i, 'child': nested}
    
    result = encode_to_dict(nested)
    
    # Verify structure is preserved
    current = result
    for i in range(depth - 1, -1, -1):
        assert 'level' in current
        assert current['level'] == i
        assert 'child' in current
        current = current['child']
    assert current == {'value': 0}


# Test with very large collections  
@given(st.integers(min_value=1000, max_value=5000))
@settings(max_examples=5)
def test_large_lists(size):
    """Test with large lists."""
    large_list = list(range(size))
    result = encode_to_dict(large_list)
    assert result == large_list
    assert len(result) == size


class InfiniteToDict:
    """A class that returns itself in to_dict - potential infinite loop."""
    def to_dict(self):
        return self


@given(st.integers(min_value=1, max_value=10))
def test_self_referential_to_dict(n):
    """Test objects that return themselves from to_dict."""
    # This should cause infinite recursion if not handled
    obj = InfiniteToDict()
    
    # This will likely cause RecursionError
    try:
        result = encode_to_dict(obj)
        # If it doesn't fail, that's actually concerning
        assert False, "Expected RecursionError but got result"
    except RecursionError:
        # This is expected behavior - the function doesn't handle this edge case
        pass


class MutatingToDict:
    """A class that mutates its return value each time to_dict is called."""
    def __init__(self):
        self.counter = 0
    
    def to_dict(self):
        self.counter += 1
        return {'count': self.counter}


@given(st.integers(min_value=1, max_value=5))
def test_mutating_to_dict(n):
    """Test objects that mutate their state in to_dict."""
    objects = [MutatingToDict() for _ in range(n)]
    
    # First encoding
    result1 = encode_to_dict(objects)
    
    # The count should be 1 for all (called once each)
    for r in result1:
        assert r['count'] == 1
    
    # Second encoding of the same objects
    result2 = encode_to_dict(objects)
    
    # Count should now be 2 (called again)
    for r in result2:
        assert r['count'] == 2


class ExceptionInToDict:
    """A class that raises an exception in to_dict."""
    def to_dict(self):
        raise ValueError("Intentional error in to_dict")


def test_exception_in_to_dict():
    """Test that exceptions in to_dict propagate correctly."""
    obj = ExceptionInToDict()
    
    try:
        encode_to_dict(obj)
        assert False, "Expected ValueError"
    except ValueError as e:
        assert "Intentional error" in str(e)


class ReturnNonDict:
    """A class that returns non-dict from to_dict."""
    def __init__(self, value):
        self.value = value
    
    def to_dict(self):
        return self.value


@given(st.one_of(
    st.integers(),
    st.text(),
    st.lists(st.integers()),
    st.none()
))
def test_non_dict_from_to_dict(value):
    """Test objects that return non-dict values from to_dict."""
    obj = ReturnNonDict(value)
    result = encode_to_dict(obj)
    
    # Should normalize whatever is returned
    assert result == encode_to_dict(value)


# Test with special float values
def test_special_floats():
    """Test with special float values."""
    special_values = [
        float('inf'),
        float('-inf'),
        float('nan'),
        0.0,
        -0.0,
        sys.float_info.max,
        sys.float_info.min,
        sys.float_info.epsilon
    ]
    
    for val in special_values:
        result = encode_to_dict(val)
        if math.isnan(val):
            assert math.isnan(result)
        else:
            assert result == val


# Test with Unicode and special strings
@given(st.text(alphabet=st.characters(min_codepoint=0x0000, max_codepoint=0x10FFFF)))
def test_unicode_strings(text):
    """Test with various Unicode strings."""
    result = encode_to_dict(text)
    assert result == text
    assert type(result) == str


class MultipleCallsToDict:
    """Test that to_dict is called exactly once per encode."""
    call_count = 0
    
    def to_dict(self):
        MultipleCallsToDict.call_count += 1
        return {'calls': MultipleCallsToDict.call_count}


def test_to_dict_called_once():
    """Verify to_dict is called exactly once during encoding."""
    MultipleCallsToDict.call_count = 0
    obj = MultipleCallsToDict()
    
    result = encode_to_dict(obj)
    assert result == {'calls': 1}
    assert MultipleCallsToDict.call_count == 1
    
    # Reset and test with nested structure
    MultipleCallsToDict.call_count = 0
    nested = {'obj': obj, 'list': [obj]}
    
    # This should call to_dict twice (once for each reference)
    result = encode_to_dict(nested)
    assert MultipleCallsToDict.call_count == 2