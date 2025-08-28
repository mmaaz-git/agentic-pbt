"""Property-based tests for sphinxcontrib.serializinghtml - Fixed version"""

import json
import tempfile
from collections import UserString
from pathlib import Path

import pytest
from hypothesis import given, strategies as st, assume

# Import module under test
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/sphinxcontrib-mermaid_env/lib/python3.13/site-packages')

from sphinxcontrib.serializinghtml import jsonimpl


# Strategy for generating JSON-serializable values
json_value = st.recursive(
    st.one_of(
        st.none(),
        st.booleans(),
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.text()
    ),
    lambda children: st.one_of(
        st.lists(children, max_size=10),
        st.dictionaries(st.text(), children, max_size=10)
    ),
    max_leaves=50
)


@given(json_value)
def test_json_round_trip_dumps_loads(data):
    """Test that jsonimpl.loads(jsonimpl.dumps(x)) == x for JSON-serializable data"""
    serialized = jsonimpl.dumps(data)
    deserialized = jsonimpl.loads(serialized)
    assert deserialized == data


@given(json_value)
def test_json_round_trip_dump_load(data):
    """Test that jsonimpl.dump/load round-trips correctly through files"""
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.json', delete=False) as f:
        jsonimpl.dump(data, f)
        f.flush()
        f.seek(0)
        loaded = jsonimpl.load(f)
        assert loaded == data


@given(st.text())
def test_userstring_serialization(text):
    """Test that UserString objects are correctly serialized"""
    user_str = UserString(text)
    
    # Test dumps
    serialized = jsonimpl.dumps(user_str)
    deserialized = jsonimpl.loads(serialized)
    assert deserialized == text
    
    # Test that it serializes the same as a regular string
    regular_serialized = jsonimpl.dumps(text)
    assert serialized == regular_serialized


@given(st.dictionaries(
    st.text(),
    st.one_of(
        st.text(),
        st.lists(st.text(), max_size=5),
        st.dictionaries(st.text(), st.text(), max_size=5)
    ),
    max_size=10
))
def test_nested_userstring_serialization(data):
    """Test that nested structures with UserString are handled correctly"""
    # Create UserString instances in the data
    def make_userstrings(obj):
        if isinstance(obj, str):
            return UserString(obj)
        elif isinstance(obj, list):
            return [make_userstrings(x) for x in obj]
        elif isinstance(obj, dict):
            return {k: make_userstrings(v) for k, v in obj.items()}
        return obj
    
    data_with_userstrings = make_userstrings(data)
    
    # Should not raise an exception
    serialized = jsonimpl.dumps(data_with_userstrings)
    
    # The result should be valid JSON
    deserialized = jsonimpl.loads(serialized)
    
    # Convert UserStrings back to regular strings for comparison
    def to_strings(obj):
        if isinstance(obj, UserString):
            return str(obj)
        elif isinstance(obj, list):
            return [to_strings(x) for x in obj]
        elif isinstance(obj, dict):
            return {k: to_strings(v) for k, v in obj.items()}
        return obj
    
    expected = to_strings(data_with_userstrings)
    assert deserialized == expected


# Test for edge cases in JSON encoding
@given(st.one_of(
    st.floats(allow_nan=False, allow_infinity=False, width=64),
    st.integers(min_value=-2**53, max_value=2**53)  # JavaScript safe integer range
))
def test_json_numeric_precision(num):
    """Test that numeric values maintain precision through serialization"""
    serialized = jsonimpl.dumps(num)
    deserialized = jsonimpl.loads(serialized)
    
    if isinstance(num, float):
        # For floats, we need to be careful about precision
        import math
        if math.isfinite(num):
            # JSON might lose some precision for floats
            assert abs(deserialized - num) < 1e-10 or deserialized == num
    else:
        assert deserialized == num


@given(st.text(alphabet=st.characters(min_codepoint=0, max_codepoint=127)))
def test_json_ascii_text_round_trip(text):
    """Test round-trip for ASCII text to avoid Unicode issues"""
    data = {"text": text, "list": [text], "nested": {"value": text}}
    serialized = jsonimpl.dumps(data)
    deserialized = jsonimpl.loads(serialized)
    assert deserialized == data


@given(st.text())
def test_json_unicode_text_round_trip(text):
    """Test round-trip for Unicode text"""
    data = {"text": text}
    serialized = jsonimpl.dumps(data)
    deserialized = jsonimpl.loads(serialized)
    assert deserialized == data


@given(st.lists(st.dictionaries(st.text(), st.text(), max_size=5), max_size=10))
def test_json_complex_structure_round_trip(data):
    """Test round-trip for more complex nested structures"""
    container = {
        "items": data,
        "count": len(data),
        "metadata": {
            "type": "test",
            "nested": {"deep": {"structure": data[:2] if len(data) >= 2 else data}}
        }
    }
    serialized = jsonimpl.dumps(container)
    deserialized = jsonimpl.loads(serialized)
    assert deserialized == container


# Test special characters and escape sequences
@given(st.text(alphabet=st.sampled_from(['"', '\\', '\n', '\r', '\t', '\b', '\f'])))
def test_json_escape_characters(text):
    """Test that special characters requiring escaping are handled correctly"""
    data = {"special": text}
    serialized = jsonimpl.dumps(data)
    deserialized = jsonimpl.loads(serialized)
    assert deserialized == data


# Test with empty structures
@given(st.one_of(
    st.just({}),
    st.just([]),
    st.just(""),
    st.just(None)
))
def test_json_empty_values(data):
    """Test serialization of empty values"""
    serialized = jsonimpl.dumps(data)
    deserialized = jsonimpl.loads(serialized)
    assert deserialized == data


# Test mixed type lists
@given(st.lists(
    st.one_of(
        st.none(),
        st.booleans(),
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.text()
    ),
    max_size=20
))
def test_json_mixed_type_lists(lst):
    """Test lists with mixed types"""
    serialized = jsonimpl.dumps(lst)
    deserialized = jsonimpl.loads(serialized)
    assert deserialized == lst


# Test deeply nested structures
@given(st.integers(min_value=1, max_value=100))
def test_json_deep_nesting(depth):
    """Test deeply nested dictionaries"""
    data = {}
    current = data
    for i in range(depth):
        current["nested"] = {}
        current = current["nested"]
    current["value"] = "deep"
    
    serialized = jsonimpl.dumps(data)
    deserialized = jsonimpl.loads(serialized)
    assert deserialized == data


# Test get_target_uri directly without mocking
def test_get_target_uri_specific_cases():
    """Test specific documented cases for get_target_uri"""
    from sphinxcontrib.serializinghtml import SerializingHTMLBuilder
    from sphinx.util.osutil import SEP
    
    # We need to test the actual method behavior
    # The method is defined in SerializingHTMLBuilder
    
    # Create a minimal subclass to test the method
    class TestBuilder(SerializingHTMLBuilder):
        def __init__(self):
            # Minimal initialization - we only need the method
            pass
    
    builder = TestBuilder()
    
    # Test case 1: 'index' returns empty string
    assert builder.get_target_uri('index') == ''
    
    # Test case 2: paths ending with SEP + 'index' have that suffix removed
    test_path = f"some/path{SEP}index"
    assert builder.get_target_uri(test_path) == test_path[:-5]
    
    # Test case 3: other paths get SEP appended
    assert builder.get_target_uri('regular/path') == f'regular/path{SEP}'
    assert builder.get_target_uri('file') == f'file{SEP}'