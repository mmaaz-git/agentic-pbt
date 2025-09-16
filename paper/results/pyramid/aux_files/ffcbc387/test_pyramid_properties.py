#!/usr/bin/env python3
"""Property-based tests for Pyramid web framework using Hypothesis."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

import math
from hypothesis import given, strategies as st, assume, settings
from pyramid import settings as pyramid_settings
from pyramid import encode, util


# Test 1: asbool idempotence property
@given(st.one_of(
    st.none(),
    st.booleans(),
    st.text(),
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False)
))
def test_asbool_idempotence(value):
    """Test that asbool is idempotent: asbool(asbool(x)) == asbool(x)"""
    first_result = pyramid_settings.asbool(value)
    second_result = pyramid_settings.asbool(first_result)
    assert second_result == first_result, f"Not idempotent for {value!r}"


# Test 2: asbool preserves boolean inputs
@given(st.booleans())
def test_asbool_preserves_booleans(value):
    """Test that boolean inputs pass through unchanged."""
    assert pyramid_settings.asbool(value) == value


# Test 3: asbool truthy strings
@given(st.sampled_from(['t', 'true', 'y', 'yes', 'on', '1', 'T', 'TRUE', 'Y', 'YES', 'ON']))
def test_asbool_truthy_strings(value):
    """Test that documented truthy strings return True."""
    assert pyramid_settings.asbool(value) is True


# Test 4: aslist empty line filtering
@given(st.text())
def test_aslist_filters_empty_lines(text):
    """Test that aslist filters out empty lines."""
    # Add some empty lines
    text_with_empty = '\n' + text + '\n\n' + text + '\n'
    result = pyramid_settings.aslist(text_with_empty)
    # Empty lines should be filtered out
    for item in result:
        assert item != '', f"Empty string found in result: {result}"


# Test 5: aslist_cronly vs aslist consistency  
@given(st.text())
def test_aslist_flatten_consistency(text):
    """Test that aslist with flatten=False matches aslist_cronly."""
    result_cronly = pyramid_settings.aslist_cronly(text)
    result_aslist = pyramid_settings.aslist(text, flatten=False)
    assert result_cronly == result_aslist


# Test 6: urlencode None value handling
@given(
    st.dictionaries(
        st.text(min_size=1),
        st.one_of(st.none(), st.text(), st.integers())
    )
)
def test_urlencode_none_values(data):
    """Test that None values in urlencode produce key= without value."""
    result = encode.urlencode(data)
    
    for key, value in data.items():
        if value is None:
            # According to v1.5 change, None values should produce "key="
            encoded_key = encode.quote_plus(key)
            assert f"{encoded_key}=" in result, f"None value for {key} not handled correctly"
            # Make sure it's not followed by another value
            assert f"{encoded_key}=None" not in result


# Test 7: urlencode handles empty dictionaries
def test_urlencode_empty_dict():
    """Test that urlencode handles empty dictionary correctly."""
    result = encode.urlencode({})
    assert result == '', f"Empty dict should produce empty string, got: {result!r}"


# Test 8: urlencode with sequences of values
@given(
    st.dictionaries(
        st.text(min_size=1, max_size=10),
        st.lists(st.text(min_size=1, max_size=10), min_size=1, max_size=3)
    )
)
def test_urlencode_with_sequences(data):
    """Test that urlencode handles sequences as values correctly (doseq=True behavior)."""
    result = encode.urlencode(data)
    
    for key, values in data.items():
        encoded_key = encode.quote_plus(key)
        for value in values:
            encoded_value = encode.quote_plus(value)
            assert f"{encoded_key}={encoded_value}" in result


# Test 9: as_sorted_tuple idempotence
@given(st.one_of(
    st.text(),
    st.integers(),
    st.lists(st.integers()),
    st.tuples(st.integers()),
    st.sets(st.integers())
))
def test_as_sorted_tuple_idempotence(value):
    """Test that as_sorted_tuple is idempotent."""
    first_result = util.as_sorted_tuple(value)
    second_result = util.as_sorted_tuple(first_result)
    assert second_result == first_result


# Test 10: as_sorted_tuple always returns sorted tuple
@given(st.lists(st.integers()))
def test_as_sorted_tuple_is_sorted(value):
    """Test that as_sorted_tuple always returns a sorted tuple."""
    result = util.as_sorted_tuple(value)
    assert isinstance(result, tuple)
    assert list(result) == sorted(result)


# Test 11: as_sorted_tuple single values become single-element tuples
@given(st.one_of(st.text(), st.integers(), st.floats(allow_nan=False)))
def test_as_sorted_tuple_single_values(value):
    """Test that single non-iterable values become single-element tuples."""
    result = util.as_sorted_tuple(value)
    assert isinstance(result, tuple)
    assert len(result) == 1
    assert result[0] == value


# Test 12: URL encoding round-trip with special characters
@given(st.text())
def test_url_quote_round_trip(text):
    """Test that URL quoting and unquoting is consistent."""
    from urllib.parse import unquote
    
    # Encode then decode
    encoded = encode.url_quote(text)
    decoded = unquote(encoded)
    
    # Should get back the original text
    assert decoded == text, f"Round-trip failed for {text!r}"


# Test 13: quote_plus handles spaces
@given(st.text(min_size=1).map(lambda x: f"text with spaces: {x}"))
def test_quote_plus_spaces(text):
    """Test that quote_plus converts spaces to +."""
    result = encode.quote_plus(text)
    # Spaces should be converted to +
    assert '+' in result, f"Spaces not converted to + in {result!r}"


# Test 14: Edge case - urlencode with None as entire query
def test_urlencode_none_query():
    """Test urlencode behavior when query is None."""
    try:
        result = encode.urlencode(None)
    except (TypeError, AttributeError) as e:
        # This is expected - None has no .items() method and is not iterable
        pass
    else:
        # If it doesn't raise, check what it returns
        assert False, f"Expected exception but got result: {result!r}"


# Test 15: aslist with mixed content
@given(st.lists(st.one_of(st.text(), st.integers())))
def test_aslist_with_non_strings(values):
    """Test aslist behavior with non-string values."""
    # When given a list, aslist should handle it
    result = pyramid_settings.aslist(values)
    assert isinstance(result, list)


# Test 16: Edge case in urlencode - prefix handling
def test_urlencode_prefix_bug():
    """Test for potential bug in urlencode's prefix handling."""
    # Looking at the code, there's a potential issue with line 76:
    # elif v is None:
    #     result += '%s%s=' % (prefix, k)
    # This line doesn't set prefix = '&' after it!
    
    data = [('a', None), ('b', 'value')]
    result = encode.urlencode(data)
    
    # Should be "a=&b=value" but might be "a=b=value" due to missing prefix update
    assert result == 'a=&b=value', f"Prefix not updated after None value: got {result!r}"


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])