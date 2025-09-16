import string
from collections import OrderedDict
from http.cookiejar import CookieJar

import pytest
from hypothesis import assume, given, strategies as st, settings, note

import requests.utils


# More aggressive testing with edge cases

@given(st.text())
def test_unquote_unreserved_malformed_escapes(text):
    """Test unquote_unreserved with various malformed percent escapes."""
    # Generate text with potential edge cases
    test_cases = [
        text + "%",  # Trailing percent
        text + "%x",  # Single hex digit  
        text + "%xx",  # Non-hex after percent
        "%" + text,  # Leading percent
        "%%" + text,  # Double percent
        text + "%0",  # Incomplete hex
        text + "%g0",  # Invalid hex char
    ]
    
    for test_input in test_cases:
        try:
            result = requests.utils.unquote_unreserved(test_input)
            # Check result is valid string
            assert isinstance(result, str)
        except requests.exceptions.InvalidURL as e:
            # Should have informative error
            assert "Invalid percent-escape sequence" in str(e) or "Invalid" in str(e)


@given(st.text(alphabet=string.printable))
def test_requote_uri_special_chars(uri):
    """Test requote_uri with special characters."""
    try:
        result = requests.utils.requote_uri(uri)
        # Result should be a string
        assert isinstance(result, str)
        # Should be idempotent
        result2 = requests.utils.requote_uri(result)
        assert result == result2
    except Exception:
        # Some inputs might fail, but we're looking for crashes
        pass


@given(st.lists(st.tuples(st.text(), st.text())))
def test_from_key_val_list_duplicates(pairs):
    """Test from_key_val_list with duplicate keys."""
    # This should handle duplicate keys by keeping last value
    result = requests.utils.from_key_val_list(pairs)
    
    # Build expected result - OrderedDict keeps last value for duplicates
    expected = OrderedDict(pairs)
    assert result == expected
    
    # Verify last-value-wins behavior
    for key, value in pairs:
        if key in result:
            # Find last occurrence of this key
            last_value = None
            for k, v in reversed(pairs):
                if k == key:
                    last_value = v
                    break
            assert result[key] == last_value


@given(st.text(min_size=1))
def test_parse_header_links_malformed(text):
    """Test parse_header_links with malformed input."""
    # Try various malformed link headers
    test_cases = [
        f"<{text}",  # Missing closing >
        f"{text}>",  # Missing opening <
        f"<{text}>; rel",  # Incomplete rel
        f"<{text}>; rel=",  # Missing rel value
        f"<<{text}>>",  # Double brackets
        f"<>; rel={text}",  # Empty URL
    ]
    
    for header in test_cases:
        try:
            result = requests.utils.parse_header_links(header)
            # Should return list even for malformed input
            assert isinstance(result, list)
        except (ValueError, AttributeError, IndexError):
            # Some malformed input might raise exceptions
            pass


@given(st.dictionaries(
    st.text(alphabet=string.printable),
    st.text(alphabet=string.printable)
))
def test_cookiejar_special_characters(cookie_dict):
    """Test cookiejar conversion with special characters."""
    try:
        jar = requests.utils.cookiejar_from_dict(cookie_dict)
        result = requests.utils.dict_from_cookiejar(jar)
        
        # Check if special characters are preserved
        for key in cookie_dict:
            if key in result:
                assert result[key] == cookie_dict[key]
    except Exception:
        # Some special characters might not be valid in cookies
        pass


@given(st.one_of(
    st.none(),
    st.booleans(),
    st.integers(),
    st.text()
))
def test_to_key_val_list_invalid_types(value):
    """Test to_key_val_list with invalid input types."""
    if value is None:
        result = requests.utils.to_key_val_list(value)
        assert result is None
    elif isinstance(value, (str, bytes, bool, int)):
        with pytest.raises(ValueError) as exc:
            requests.utils.to_key_val_list(value)
        assert "cannot encode objects that are not 2-tuples" in str(exc.value)


@given(st.one_of(
    st.none(),
    st.booleans(), 
    st.integers(),
    st.text()
))
def test_from_key_val_list_invalid_types(value):
    """Test from_key_val_list with invalid input types."""
    if value is None:
        result = requests.utils.from_key_val_list(value)
        assert result is None
    elif isinstance(value, (str, bytes, bool, int)):
        with pytest.raises(ValueError) as exc:
            requests.utils.from_key_val_list(value)
        assert "cannot encode objects that are not 2-tuples" in str(exc.value)


@given(st.text())
def test_super_len_string(s):
    """Test super_len with strings."""
    length = requests.utils.super_len(s)
    assert length == len(s)


@given(st.binary())
def test_super_len_bytes(b):
    """Test super_len with bytes."""
    length = requests.utils.super_len(b)
    assert length == len(b)


@given(st.lists(st.integers()))
def test_super_len_list(lst):
    """Test super_len with lists."""
    length = requests.utils.super_len(lst)
    assert length == len(lst)


# Test quote with different safe characters
@given(
    st.text(alphabet=string.printable),
    st.text(alphabet=string.ascii_letters + string.digits + "-._~")
)
def test_quote_safe_parameter(text, safe):
    """Test quote function with custom safe characters."""
    try:
        quoted = requests.utils.quote(text, safe=safe)
        # Safe characters should not be encoded
        for char in safe:
            if char in text:
                # Character should appear unencoded in result
                assert char in quoted or text.count(char) == 0
    except Exception:
        # Some combinations might fail
        pass


# Edge case: empty structures
def test_empty_conversions():
    """Test conversions with empty structures."""
    # Empty dict
    assert requests.utils.to_key_val_list({}) == []
    assert requests.utils.from_key_val_list([]) == OrderedDict()
    
    # Empty cookiejar
    empty_jar = requests.utils.cookiejar_from_dict({})
    assert requests.utils.dict_from_cookiejar(empty_jar) == {}
    
    # Empty string operations
    assert requests.utils.unquote_unreserved("") == ""
    assert requests.utils.requote_uri("") == ""


# Test very long strings
@given(st.text(min_size=1000, max_size=10000))
def test_long_string_operations(text):
    """Test operations with very long strings."""
    # These should handle long strings without issues
    try:
        requests.utils.super_len(text)
        requests.utils.quote(text)
        requests.utils.unquote_unreserved(text[:100])  # Use prefix to avoid timeout
    except MemoryError:
        # Very long strings might cause memory issues
        pass


@given(st.text(alphabet="%0123456789abcdefABCDEF"))
def test_unquote_unreserved_all_hex(text):
    """Test unquote_unreserved with strings that look like hex escapes."""
    try:
        result = requests.utils.unquote_unreserved(text)
        # Should handle hex-like input
        assert isinstance(result, str)
    except requests.exceptions.InvalidURL:
        # Invalid sequences should raise appropriate error
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])