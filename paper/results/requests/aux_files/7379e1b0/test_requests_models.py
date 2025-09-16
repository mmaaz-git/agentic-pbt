"""Property-based tests for requests.models module."""

import codecs
from hypothesis import given, strategies as st, assume, settings, HealthCheck
import requests.models


@given(st.dictionaries(st.text(min_size=1), st.text()))
def test_case_insensitive_dict_invariant(data):
    """Test that CaseInsensitiveDict provides case-insensitive access as documented."""
    cid = requests.models.CaseInsensitiveDict(data)
    
    for key in data:
        # Test that different case variations return the same value
        assert cid.get(key) == cid.get(key.lower())
        assert cid.get(key) == cid.get(key.upper())
        
        # Test containment with different cases
        if key:  # Skip empty keys
            assert (key in cid) == (key.lower() in cid)
            assert (key in cid) == (key.upper() in cid)


@given(st.text())
def test_requote_uri_idempotence(uri):
    """Test that requote_uri is idempotent - applying twice equals applying once."""
    try:
        quoted_once = requests.models.requote_uri(uri)
        quoted_twice = requests.models.requote_uri(quoted_once)
        assert quoted_once == quoted_twice
    except (ValueError, UnicodeError):
        # Some URIs might be invalid, that's OK
        pass


@given(st.dictionaries(st.text(min_size=1), st.text()))
def test_to_key_val_list_dict_conversion(data):
    """Test that to_key_val_list correctly converts dictionaries."""
    result = requests.models.to_key_val_list(data)
    
    # Result should be a list of tuples
    assert isinstance(result, list)
    assert all(isinstance(item, tuple) and len(item) == 2 for item in result)
    
    # Converting back to dict should preserve the data
    result_dict = dict(result)
    assert result_dict == data


@given(st.lists(st.tuples(st.text(), st.text())))
def test_to_key_val_list_tuple_list_passthrough(data):
    """Test that to_key_val_list passes through lists of tuples unchanged."""
    result = requests.models.to_key_val_list(data)
    assert result == data


@given(st.text())
def test_parse_header_links_robustness(header_value):
    """Test that parse_header_links doesn't crash on arbitrary input."""
    result = requests.models.parse_header_links(header_value)
    # Should always return a list
    assert isinstance(result, list)


@given(st.text().filter(lambda x: x.strip(" '\"") == ""))
@settings(suppress_health_check=[HealthCheck.filter_too_much])
def test_parse_header_links_empty_string_variations(text):
    """Test parse_header_links handles strings that become empty after stripping."""
    # Test with strings that are just whitespace and quotes
    result = requests.models.parse_header_links(text)
    assert result == []


# Generate JSON-like byte sequences with different encodings
json_bytes_strategy = st.one_of(
    # UTF-8
    st.text(alphabet=st.characters(codec='utf-8'), min_size=2).map(lambda s: ('{"test":"' + s + '"}').encode('utf-8')),
    # UTF-16 LE/BE
    st.text(min_size=2).map(lambda s: ('{"test":"' + s + '"}').encode('utf-16le')),
    st.text(min_size=2).map(lambda s: ('{"test":"' + s + '"}').encode('utf-16be')),
    # UTF-32 LE/BE
    st.text(min_size=2).map(lambda s: ('{"test":"' + s + '"}').encode('utf-32le')),
    st.text(min_size=2).map(lambda s: ('{"test":"' + s + '"}').encode('utf-32be')),
    # With BOM
    st.text(min_size=2).map(lambda s: codecs.BOM_UTF8 + ('{"test":"' + s + '"}').encode('utf-8')),
    st.text(min_size=2).map(lambda s: codecs.BOM_UTF32_LE + ('{"test":"' + s + '"}').encode('utf-32le')),
    st.text(min_size=2).map(lambda s: codecs.BOM_UTF32_BE + ('{"test":"' + s + '"}').encode('utf-32be')),
)


@given(json_bytes_strategy)
def test_guess_json_utf_returns_valid_encoding(data):
    """Test that guess_json_utf returns a valid encoding string."""
    result = requests.models.guess_json_utf(data)
    
    # Should return a string
    assert isinstance(result, str)
    
    # Should be a known encoding
    known_encodings = ['utf-8', 'utf-8-sig', 'utf-16', 'utf-16-be', 'utf-16-le', 
                       'utf-32', 'utf-32-be', 'utf-32-le']
    assert result in known_encodings


@given(st.binary(min_size=4))
def test_guess_json_utf_arbitrary_bytes(data):
    """Test that guess_json_utf doesn't crash on arbitrary byte sequences."""
    result = requests.models.guess_json_utf(data)
    # Should always return a string or None
    assert result is None or isinstance(result, str)


@given(st.tuples(st.text(min_size=1), st.text()))
def test_check_header_validity_basic(header):
    """Test check_header_validity doesn't crash on arbitrary headers."""
    try:
        requests.models.check_header_validity(header)
        # If it doesn't raise, the header is valid
        header_name, header_value = header
        
        # Valid headers shouldn't have these issues
        assert not header_name.startswith(' ')
        assert not header_name.startswith('\t')
        assert '\r' not in header_name
        assert '\n' not in header_name
        
    except Exception as e:
        # Check if it's an InvalidHeader exception
        if 'InvalidHeader' in str(type(e).__name__):
            pass  # Expected for invalid headers
        else:
            raise  # Unexpected exception


@given(st.dictionaries(st.text(min_size=1), st.text()))
def test_cookiejar_from_dict_round_trip(cookie_dict):
    """Test cookiejar_from_dict creates a valid CookieJar."""
    jar = requests.models.cookiejar_from_dict(cookie_dict)
    
    # Should be able to iterate over the jar
    cookies = {}
    for cookie in jar:
        cookies[cookie.name] = cookie.value
    
    # All original cookies should be present
    for key, value in cookie_dict.items():
        if key:  # Skip empty keys which might be invalid cookie names
            assert key in cookies