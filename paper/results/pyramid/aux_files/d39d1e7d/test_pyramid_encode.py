"""Property-based testing for pyramid.encode module."""

import math
import sys
import os
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from urllib.parse import unquote, unquote_plus, parse_qs, parse_qsl
from hypothesis import assume, given, strategies as st, settings
from pyramid.encode import url_quote, quote_plus, urlencode


@given(st.dictionaries(
    st.text(min_size=1),
    st.one_of(st.none(), st.text(), st.integers(), st.floats(allow_nan=False, allow_infinity=False))
))
def test_urlencode_drops_none_values(query):
    """Test that None values are dropped from urlencode output."""
    result = urlencode(query)
    
    # Count None values in input
    none_count = sum(1 for v in query.values() if v is None)
    
    # If there are None values, they should not appear in the output
    if none_count > 0:
        # None values should result in "key=" with no value
        for key, value in query.items():
            if value is None:
                encoded_key = quote_plus(str(key))
                # Check that we have key= but not key=None
                assert f"{encoded_key}=" in result
                assert f"{encoded_key}=None" not in result


@given(st.dictionaries(
    st.text(min_size=1),
    st.lists(st.one_of(st.text(), st.integers()), min_size=1, max_size=5)
))
def test_urlencode_expands_iterables(query):
    """Test that non-string iterables are expanded into multiple key=value pairs."""
    result = urlencode(query)
    
    for key, values in query.items():
        encoded_key = quote_plus(str(key))
        # Each value in the list should appear in the result
        for value in values:
            encoded_value = quote_plus(str(value))
            assert f"{encoded_key}={encoded_value}" in result
        
        # Count occurrences of the key
        key_count = result.count(f"{encoded_key}=")
        assert key_count == len(values)


@given(st.one_of(
    st.dictionaries(st.text(min_size=1), st.text()),
    st.lists(st.tuples(st.text(min_size=1), st.text()))
))
def test_urlencode_handles_dict_and_tuples(query):
    """Test that urlencode handles both dict and list of tuples."""
    result = urlencode(query)
    
    # Should not raise an exception and should return a string
    assert isinstance(result, str)
    
    # Check basic structure
    if query:  # non-empty
        assert '=' in result or result == ''
        
        # For lists of tuples, order should be preserved
        if isinstance(query, list):
            # Build expected pairs
            expected_pairs = []
            for k, v in query:
                expected_pairs.append((quote_plus(str(k)), quote_plus(str(v))))
            
            # Check that pairs appear in order
            result_pairs = result.split('&') if result else []
            for i, pair in enumerate(result_pairs):
                if '=' in pair:
                    parts = pair.split('=', 1)
                    if i < len(expected_pairs):
                        assert parts[0] == expected_pairs[i][0]


@given(st.one_of(
    st.text(),
    st.binary(),
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False)
))
def test_url_quote_handles_types(value):
    """Test that url_quote handles different types correctly."""
    result = url_quote(value)
    
    # Should always return a string
    assert isinstance(result, str)
    
    # Should be URL-safe (no spaces, etc)
    assert ' ' not in result
    
    # For strings and bytes, should preserve content after encoding
    if isinstance(value, (str, bytes)):
        if isinstance(value, str):
            # Unicode strings should be UTF-8 encoded
            unquoted = unquote(result, encoding='utf-8')
            assert unquoted == value
        elif isinstance(value, bytes):
            # Bytes should be decoded as UTF-8 for the comparison
            try:
                original_str = value.decode('utf-8')
                unquoted = unquote(result, encoding='utf-8')
                assert unquoted == original_str
            except UnicodeDecodeError:
                # If bytes aren't valid UTF-8, that's ok
                pass


@given(st.one_of(
    st.text(),
    st.binary(),
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False)
))
def test_quote_plus_handles_types(value):
    """Test that quote_plus handles different types correctly."""
    result = quote_plus(value)
    
    # Should always return a string
    assert isinstance(result, str)
    
    # Should be URL-safe (spaces become +)
    assert ' ' not in result
    
    # For strings and bytes, should preserve content after encoding
    if isinstance(value, (str, bytes)):
        if isinstance(value, str):
            # Unicode strings should be UTF-8 encoded
            unquoted = unquote_plus(result, encoding='utf-8')
            assert unquoted == value
        elif isinstance(value, bytes):
            # Bytes should be decoded as UTF-8 for the comparison
            try:
                original_str = value.decode('utf-8')
                unquoted = unquote_plus(result, encoding='utf-8')
                assert unquoted == original_str
            except UnicodeDecodeError:
                # If bytes aren't valid UTF-8, that's ok
                pass


@given(st.text())
def test_quote_plus_spaces_to_plus(text):
    """Test that quote_plus converts spaces to + signs."""
    assume(' ' in text)
    result = quote_plus(text)
    
    # Spaces should become +
    assert '+' in result or '%20' in result
    assert ' ' not in result


@given(st.dictionaries(
    st.text(min_size=1),
    st.one_of(
        st.text(),
        st.lists(st.text(), min_size=1, max_size=3),
        st.none()
    ),
    min_size=1,
    max_size=10
))
def test_urlencode_empty_values_and_structure(query):
    """Test urlencode produces valid query string structure."""
    result = urlencode(query)
    
    # Should be a valid query string format
    if result:
        pairs = result.split('&')
        for pair in pairs:
            # Each pair should have exactly one = 
            assert pair.count('=') == 1
            key, value = pair.split('=')
            # Keys should never be empty
            assert key != ''


@given(
    st.lists(
        st.tuples(
            st.text(min_size=1),
            st.one_of(st.text(), st.none())
        ),
        min_size=1
    )
)
def test_urlencode_preserves_order_for_tuples(query):
    """Test that urlencode preserves order when given list of tuples."""
    result = urlencode(query)
    
    if not result:
        return
    
    # Extract keys from result in order
    result_keys = []
    for pair in result.split('&'):
        if '=' in pair:
            key = pair.split('=')[0]
            result_keys.append(key)
    
    # Extract expected keys in order (accounting for None values)
    expected_keys = []
    for k, v in query:
        encoded_k = quote_plus(str(k))
        expected_keys.append(encoded_k)
    
    # Keys should appear in the same order
    assert result_keys == expected_keys


@given(st.dictionaries(
    st.text(min_size=1, alphabet=st.characters(min_codepoint=0x0, max_codepoint=0x10ffff, blacklist_characters='\x00')),
    st.text(alphabet=st.characters(min_codepoint=0x0, max_codepoint=0x10ffff, blacklist_characters='\x00')),
    min_size=1,
    max_size=5
))
def test_urlencode_unicode_handling(query):
    """Test that urlencode handles Unicode correctly."""
    result = urlencode(query)
    
    # Should not raise exceptions with Unicode
    assert isinstance(result, str)
    
    # Parse it back
    parsed = parse_qs(result)
    
    # Check that all non-None values round-trip
    for key, value in query.items():
        if value is not None:
            # parse_qs returns lists of values
            assert key in parsed
            assert str(value) in parsed[key]


@given(st.text(min_size=1), st.text())
def test_url_quote_safe_parameter(text, safe):
    """Test that url_quote respects the safe parameter."""
    result = url_quote(text, safe=safe)
    
    # Characters in safe should not be encoded
    for char in safe:
        if char in text:
            # The character should appear unencoded in result
            # (unless it's a special char that must be encoded)
            if char not in '%':
                assert char in result or char not in text