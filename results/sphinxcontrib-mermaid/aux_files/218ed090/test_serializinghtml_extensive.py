"""Extensive property-based tests for sphinxcontrib.serializinghtml"""

import json
import tempfile
from collections import UserString
from pathlib import Path

import pytest
from hypothesis import given, strategies as st, assume, settings

# Import module under test
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/sphinxcontrib-mermaid_env/lib/python3.13/site-packages')

from sphinxcontrib.serializinghtml import jsonimpl


# More extensive test with larger datasets
@given(st.lists(
    st.dictionaries(
        st.text(min_size=1, max_size=100),
        st.one_of(
            st.none(),
            st.booleans(),
            st.integers(min_value=-10**10, max_value=10**10),
            st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10),
            st.text(max_size=1000)
        ),
        min_size=1,
        max_size=50
    ),
    min_size=1,
    max_size=100
))
@settings(max_examples=500)
def test_large_json_structures(data):
    """Test with larger, more complex JSON structures"""
    serialized = jsonimpl.dumps(data)
    deserialized = jsonimpl.loads(serialized)
    assert deserialized == data


# Test UserString with special characters
@given(st.text(alphabet=st.characters(blacklist_categories=('Cs',))))
@settings(max_examples=500)
def test_userstring_with_special_chars(text):
    """Test UserString with various Unicode characters"""
    user_str = UserString(text)
    serialized = jsonimpl.dumps(user_str)
    deserialized = jsonimpl.loads(serialized)
    assert deserialized == text


# Test edge cases with numeric values
@given(st.one_of(
    st.floats(allow_nan=True, allow_infinity=True),
    st.floats(min_value=-1e308, max_value=1e308),
    st.integers(min_value=-2**63, max_value=2**63-1)
))
@settings(max_examples=500)
def test_numeric_edge_cases(num):
    """Test edge cases for numeric serialization"""
    import math
    
    # jsonimpl allows NaN and Infinity (unlike strict JSON)
    serialized = jsonimpl.dumps(num)
    deserialized = jsonimpl.loads(serialized)
    
    if math.isnan(num):
        assert math.isnan(deserialized)
    elif math.isinf(num):
        assert math.isinf(deserialized) and (num > 0) == (deserialized > 0)
    elif isinstance(num, float) and abs(num) > 1e15:
        # Large floats might lose precision
        assert abs((deserialized - num) / num) < 1e-10 if num != 0 else deserialized == 0
    else:
        assert deserialized == num


# Test with circular references (should fail)
def test_circular_reference_handling():
    """Test that circular references are handled appropriately"""
    data = {}
    data['self'] = data
    
    # JSON can't handle circular references
    with pytest.raises(ValueError):
        jsonimpl.dumps(data)


# Test with very deeply nested UserStrings
@given(st.integers(min_value=1, max_value=50))
@settings(max_examples=100)
def test_deeply_nested_userstrings(depth):
    """Test deeply nested structures with UserStrings"""
    data = {"value": UserString("test")}
    current = data
    
    for i in range(depth):
        current["nested"] = {"value": UserString(f"level_{i}")}
        current = current["nested"]
    
    serialized = jsonimpl.dumps(data)
    deserialized = jsonimpl.loads(serialized)
    
    # Verify the structure is preserved
    current_check = deserialized
    for i in range(depth):
        assert "nested" in current_check
        current_check = current_check["nested"]


# Test file operations with various encodings
@given(st.text())
@settings(max_examples=200)
def test_file_dump_load_with_unicode(text):
    """Test file operations with Unicode content"""
    data = {"unicode_text": text, "nested": {"value": text}}
    
    with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8', suffix='.json', delete=False) as f:
        jsonimpl.dump(data, f)
        f.flush()
        f.seek(0)
        loaded = jsonimpl.load(f)
        assert loaded == data


# Test mixed UserString and regular strings
@given(st.lists(st.booleans(), min_size=1, max_size=20))
@settings(max_examples=200)
def test_mixed_userstring_regular_strings(use_userstring_flags):
    """Test mixing UserString and regular strings in the same structure"""
    data = []
    for i, use_userstring in enumerate(use_userstring_flags):
        value = f"value_{i}"
        if use_userstring:
            data.append(UserString(value))
        else:
            data.append(value)
    
    container = {"mixed": data}
    serialized = jsonimpl.dumps(container)
    deserialized = jsonimpl.loads(serialized)
    
    # All should be regular strings after deserialization
    expected = {"mixed": [f"value_{i}" for i in range(len(use_userstring_flags))]}
    assert deserialized == expected


# Test with bytes-like data (should fail as JSON doesn't support bytes)
def test_bytes_serialization():
    """Test that bytes objects raise appropriate errors"""
    data = {"bytes": b"test"}
    
    # JSON can't serialize bytes directly
    with pytest.raises(TypeError):
        jsonimpl.dumps(data)


# Test empty UserString
def test_empty_userstring():
    """Test serialization of empty UserString"""
    empty_user_str = UserString("")
    serialized = jsonimpl.dumps(empty_user_str)
    deserialized = jsonimpl.loads(serialized)
    assert deserialized == ""
    assert serialized == '""'


# Test UserString with JSON special strings
@given(st.sampled_from(["null", "true", "false", "NaN", "Infinity", "-Infinity"]))
def test_userstring_json_keywords(keyword):
    """Test UserString containing JSON keywords"""
    user_str = UserString(keyword)
    serialized = jsonimpl.dumps(user_str)
    deserialized = jsonimpl.loads(serialized)
    assert deserialized == keyword
    # Should be quoted as a string, not interpreted as JSON keyword
    assert serialized == f'"{keyword}"'