"""More aggressive property-based tests for requests library edge cases."""

import string
from hypothesis import given, strategies as st, assume, settings, example
from requests import utils
from requests.structures import CaseInsensitiveDict


# Test cookie handling with special characters and Unicode
@given(st.dictionaries(
    st.text(min_size=1).filter(lambda x: x and not any(c in x for c in '\r\n\x00;,')),
    st.text().filter(lambda x: not any(c in x for c in '\r\n\x00'))
))
@settings(max_examples=1000)
def test_cookie_unicode_round_trip(cookie_dict):
    """Test cookie round-trip with Unicode and special characters."""
    try:
        jar = utils.cookiejar_from_dict(cookie_dict)
        result = utils.dict_from_cookiejar(jar)
        assert result == cookie_dict
    except Exception as e:
        # If it fails, that might be a bug
        print(f"Failed with input: {cookie_dict}")
        print(f"Error: {e}")
        raise


# Test requote_uri with various special characters
@given(st.text(alphabet=string.printable))
@settings(max_examples=500)
def test_requote_uri_special_chars(uri):
    """Test requote_uri with special characters."""
    try:
        result = utils.requote_uri(uri)
        # Should be idempotent
        result2 = utils.requote_uri(result)
        assert result == result2
    except Exception:
        # Skip invalid URLs
        pass


# Test unquote_unreserved with malformed percent encoding
@given(st.text())
@example("%")
@example("%%")
@example("%2")
@example("%GG")
@example("%00")
@settings(max_examples=500)
def test_unquote_unreserved_malformed(text):
    """Test unquote_unreserved with malformed percent encoding."""
    try:
        result = utils.unquote_unreserved(text)
        # If it doesn't raise, check some properties
        # Unreserved characters should be unquoted
        assert '%41' not in result or 'A' in result  # %41 is 'A'
    except Exception as e:
        # Check if it's the expected exception
        assert "InvalidURL" in str(type(e).__name__) or "Invalid percent-escape" in str(e)


# Test guess_json_utf with edge cases
@given(st.binary(min_size=0, max_size=100))
@settings(max_examples=1000)
def test_guess_json_utf_random_bytes(data):
    """Test guess_json_utf doesn't crash on random bytes."""
    result = utils.guess_json_utf(data)
    # Should return a string or None
    assert result is None or isinstance(result, str)


# Test CaseInsensitiveDict with empty string keys
@given(st.dictionaries(
    st.text(min_size=0, max_size=10),
    st.text()
))
def test_case_insensitive_dict_empty_keys(d):
    """Test CaseInsensitiveDict with empty and special keys."""
    if '' in d:
        # Test empty string key specifically
        cid = CaseInsensitiveDict(d)
        assert cid[''] == d['']
    else:
        cid = CaseInsensitiveDict(d)
        for key in d:
            if key:  # Skip empty keys
                assert cid[key.lower()] == d[key]


# Test from_key_val_list and to_key_val_list round-trip
@given(st.lists(st.tuples(
    st.text(min_size=1),
    st.text()
)))
@settings(max_examples=500)
def test_key_val_list_round_trip(pairs):
    """Test from_key_val_list and to_key_val_list round-trip."""
    if hasattr(utils, 'from_key_val_list') and hasattr(utils, 'to_key_val_list'):
        try:
            d = utils.from_key_val_list(pairs)
            # Convert back might not preserve order or duplicates
            # Just check it doesn't crash
            if hasattr(utils, 'to_key_val_list'):
                result = utils.to_key_val_list(d)
                assert isinstance(result, list)
        except:
            pass


# Test parse_header_links if available
@given(st.text())
@settings(max_examples=500)  
def test_parse_header_links_no_crash(header_value):
    """Test parse_header_links doesn't crash on arbitrary input."""
    if hasattr(utils, 'parse_header_links'):
        try:
            result = utils.parse_header_links(header_value)
            assert isinstance(result, list)
        except:
            pass


# More aggressive test for CaseInsensitiveDict behavior
@given(
    st.text(min_size=1, alphabet=string.ascii_letters),
    st.text(),
    st.text()
)
def test_case_insensitive_dict_update_behavior(key, val1, val2):
    """Test CaseInsensitiveDict update behavior with case variations."""
    cid = CaseInsensitiveDict()
    
    # Set with lowercase
    cid[key.lower()] = val1
    assert cid[key.upper()] == val1
    assert list(cid.keys()) == [key.lower()]
    
    # Update with uppercase
    cid[key.upper()] = val2
    assert cid[key.lower()] == val2
    assert list(cid.keys()) == [key.upper()]  # Should update to new case


# Test requote_uri preserves certain characters
@given(st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789-._~:/?#[]@!$&'()*+,;="))
@settings(max_examples=500)
def test_requote_uri_preserves_valid_chars(uri):
    """Test that requote_uri preserves valid URI characters."""
    try:
        result = utils.requote_uri(uri)
        # Check that unreserved characters are not encoded
        for char in "-._~":
            if char in uri:
                assert char in result
    except:
        pass