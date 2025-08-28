#!/usr/bin/env python3
"""Property-based tests for fire.console module."""

import os
import sys
import string
import random
from hypothesis import given, strategies as st, assume, settings
import pytest

# Add fire_env to path
sys.path.insert(0, '/root/hypothesis-llm/envs/fire_env/lib/python3.13/site-packages')

from fire.console import encoding
from fire.console import text
from fire.console import files


# Test 1: Encode/Decode round-trip property
@given(st.text())
def test_encode_decode_roundtrip(s):
    """Test that Decode(Encode(s)) == s for any string."""
    encoded = encoding.Encode(s)
    decoded = encoding.Decode(encoded)
    assert decoded == s


# Test 2: Decode handles None correctly
@given(st.none())
def test_decode_none(value):
    """Test that Decode(None) returns None as documented."""
    assert encoding.Decode(value) is None


# Test 3: TypedText length property
@given(st.lists(st.text(), min_size=1, max_size=10))
def test_typed_text_length(texts):
    """Test that TypedText.__len__ returns sum of text lengths."""
    typed_text = text.TypedText(texts)
    expected_length = sum(len(t) for t in texts)
    assert len(typed_text) == expected_length


# Test 4: TypedText addition preserves length
@given(st.text(), st.text())
def test_typed_text_addition_length(text1, text2):
    """Test that adding TypedText objects preserves total length."""
    t1 = text.TypedText([text1])
    t2 = text.TypedText([text2])
    combined = t1 + t2
    assert len(combined) == len(t1) + len(t2)


# Test 5: TypedText radd (reverse add) preserves length
@given(st.text(), st.text())  
def test_typed_text_radd_length(text1, text2):
    """Test that reverse adding with TypedText preserves length."""
    t = text.TypedText([text2])
    combined = text1 + t  # This triggers __radd__
    assert len(combined) == len(text1) + len(t)


# Test 6: TypedText nested addition
@given(st.lists(st.text(), min_size=2, max_size=5))
def test_typed_text_nested_addition(texts):
    """Test nested TypedText additions maintain correct length."""
    typed_texts = [text.TypedText([t]) for t in texts]
    result = typed_texts[0]
    for tt in typed_texts[1:]:
        result = result + tt
    expected_length = sum(len(t) for t in texts)
    assert len(result) == expected_length


# Test 7: FindExecutableOnPath with path component should raise ValueError
@given(st.text(min_size=1).filter(lambda x: '/' in x or '\\' in x))
def test_find_executable_with_path_raises(executable):
    """Test that FindExecutableOnPath raises ValueError when executable has a path."""
    with pytest.raises(ValueError, match="must not have a path"):
        files.FindExecutableOnPath(executable)


# Test 8: FindExecutableOnPath with extension should raise ValueError (when not allowed)
@given(st.text(min_size=2).map(lambda x: x + '.exe'))
def test_find_executable_with_extension_raises(executable):
    """Test that FindExecutableOnPath raises ValueError when executable has extension."""
    with pytest.raises(ValueError, match="must not have an extension"):
        files.FindExecutableOnPath(executable, allow_extensions=False)


# Test 9: _FindExecutableOnPath with string pathext should raise ValueError
@given(st.text(min_size=1).filter(lambda x: '/' not in x and '\\' not in x),
       st.text(), 
       st.text())
def test_find_executable_internal_string_pathext_raises(executable, path, pathext):
    """Test that _FindExecutableOnPath raises ValueError when pathext is a string."""
    assume(not os.path.dirname(executable))  # Ensure no path component
    with pytest.raises(ValueError, match="pathext must be an iterable of strings"):
        files._FindExecutableOnPath(executable, path, pathext)


# Test 10: GetEncodedValue/SetEncodedValue round-trip
@given(st.text(min_size=1), st.text())
def test_env_encoding_roundtrip(name, value):
    """Test that SetEncodedValue/GetEncodedValue work as a round-trip."""
    env = {}
    encoding.SetEncodedValue(env, name, value)
    retrieved = encoding.GetEncodedValue(env, name)
    assert retrieved == value


# Test 11: SetEncodedValue with None removes the key
@given(st.text(min_size=1), st.text())
def test_set_encoded_value_none_removes(name, initial_value):
    """Test that SetEncodedValue with None removes the environment variable."""
    env = {}
    encoding.SetEncodedValue(env, name, initial_value)
    assert encoding.GetEncodedValue(env, name) == initial_value
    encoding.SetEncodedValue(env, name, None)
    assert encoding.GetEncodedValue(env, name) is None
    assert encoding.GetEncodedValue(env, name, "default") == "default"


# Test 12: Decode handles various input types
@given(st.one_of(st.text(), st.binary(), st.integers()))
def test_decode_various_types(data):
    """Test that Decode handles various input types without crashing."""
    result = encoding.Decode(data)
    assert isinstance(result, str) or result is None


# Test 13: TypedText with nested TypedText objects
@given(st.lists(st.text(), min_size=1, max_size=5))
def test_typed_text_nested_texts(texts):
    """Test TypedText with mixture of strings and TypedText objects."""
    mixed = []
    for i, t in enumerate(texts):
        if i % 2 == 0:
            mixed.append(t)
        else:
            mixed.append(text.TypedText([t]))
    
    typed_text = text.TypedText(mixed)
    expected_length = sum(len(t) for t in texts)
    assert len(typed_text) == expected_length


if __name__ == "__main__":
    print("Running property-based tests for fire.console...")
    pytest.main([__file__, "-v"])