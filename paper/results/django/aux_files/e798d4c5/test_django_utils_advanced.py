"""Advanced property-based tests for django.utils - looking for edge cases"""

import re
from hypothesis import given, strategies as st, assume, settings, example
from django.utils import encoding, text, html, datastructures, http, dateparse
import datetime


# Test for potential issues with special Unicode characters
@given(st.text(alphabet=st.characters(blacklist_categories=('Cc', 'Cs'))))
def test_force_bytes_str_with_errors(s):
    """Test force_bytes/force_str with different error handling"""
    # Test with 'strict' error handling (default)
    as_bytes = encoding.force_bytes(s, errors='strict')
    back_to_str = encoding.force_str(as_bytes, errors='strict')
    assert back_to_str == s
    
    # Test with 'replace' error handling
    as_bytes_replace = encoding.force_bytes(s, errors='replace')
    back_to_str_replace = encoding.force_str(as_bytes_replace, errors='replace')
    # With replace, we might lose data but shouldn't crash


# Test slugify with special characters and edge cases
@given(st.text())
@example("--hello--world--")  # Multiple dashes
@example("___test___")  # Multiple underscores  
@example("-")  # Just a dash
@example("_")  # Just underscore
@example("   ")  # Just spaces
def test_slugify_edge_cases(s):
    """Test slugify with edge cases"""
    result = text.slugify(s)
    # Result should never start or end with - or _
    if result:
        assert not result.startswith('-')
        assert not result.startswith('_') 
        assert not result.endswith('-')
        assert not result.endswith('_')
    # Double check idempotence even for edge cases
    assert text.slugify(result) == result


# Test for potential XSS issues in html.escape
@given(st.text())
def test_html_escape_comprehensive(s):
    """Test html.escape handles all dangerous patterns"""
    escaped = str(html.escape(s))
    
    # Check for common XSS patterns that should be escaped
    dangerous_patterns = [
        '<script',
        '<img',
        'javascript:',
        'onerror=',
        'onclick=',
        '<iframe',
        '<!--',
        '<svg',
        '<object',
        '<embed',
        '<applet'
    ]
    
    for pattern in dangerous_patterns:
        assert pattern.lower() not in escaped.lower()


# Test http.urlencode and parse_qsl round-trip
@given(
    st.dictionaries(
        st.text(alphabet=st.characters(min_codepoint=32, max_codepoint=126), min_size=1).filter(lambda x: '&' not in x and '=' not in x),
        st.text(alphabet=st.characters(min_codepoint=32, max_codepoint=126)).filter(lambda x: '&' not in x and '=' not in x),
        min_size=1
    )
)
def test_urlencode_roundtrip(params):
    """Test that urlencode/parse_qsl are inverse operations"""
    from urllib.parse import parse_qsl
    
    # Encode the parameters
    encoded = http.urlencode(params)
    
    # Decode them back
    decoded = dict(parse_qsl(encoded))
    
    # Should get back the same dictionary
    assert decoded == params


# Test for MultiValueDict edge cases
@given(
    st.text(min_size=1),
    st.lists(st.text(), min_size=0, max_size=10)
)
def test_multivalue_dict_empty_list(key, values):
    """Test MultiValueDict with empty and non-empty lists"""
    mvd = datastructures.MultiValueDict()
    mvd.setlist(key, values)
    
    retrieved = mvd.getlist(key)
    assert retrieved == values
    
    # If we set an empty list, getlist should return empty list, not None
    if not values:
        assert retrieved == []
        assert mvd.getlist(key) == []


# Test text.get_text_list formatting
@given(
    st.lists(st.text(min_size=1), min_size=0, max_size=5)
)
def test_get_text_list_invariants(items):
    """Test that get_text_list produces valid output"""
    result = text.get_text_list(items, 'and')
    
    if not items:
        assert result == ''
    elif len(items) == 1:
        assert result == items[0]
    else:
        # All items should appear in the result
        for item in items:
            assert item in result
        # Should contain the conjunction
        assert 'and' in result


# Test text.compress_string and decompress round-trip
@given(st.binary(min_size=1))
def test_compress_decompress_roundtrip(data):
    """Test that compress/decompress are inverse operations"""
    import gzip
    
    compressed = text.compress_string(data)
    
    # Decompress using gzip
    decompressed = gzip.decompress(compressed)
    
    assert decompressed == data


# Test dateparse functions with valid inputs
@given(
    st.integers(min_value=1, max_value=9999),  # year
    st.integers(min_value=1, max_value=12),    # month  
    st.integers(min_value=1, max_value=28)     # day (28 to avoid month issues)
)
def test_dateparse_date_roundtrip(year, month, day):
    """Test parse_date with valid date strings"""
    date_obj = datetime.date(year, month, day)
    date_str = date_obj.isoformat()
    
    parsed = dateparse.parse_date(date_str)
    assert parsed == date_obj


# Test ImmutableList truly is immutable
@given(st.lists(st.integers()))
def test_immutable_list_immutability(items):
    """Test that ImmutableList raises errors on mutation attempts"""
    immutable = datastructures.ImmutableList(items)
    
    # Should be able to read
    assert list(immutable) == items
    
    if items:
        # Should not be able to modify
        try:
            immutable[0] = 999
            assert False, "Should have raised error on assignment"
        except (TypeError, AttributeError):
            pass  # Expected
            
        try:
            immutable.append(999)
            assert False, "Should have raised error on append"
        except AttributeError:
            pass  # Expected


# Test for potential issues with URI encoding edge cases
@given(st.text())
def test_iri_to_uri_safety(iri):
    """Test that iri_to_uri always produces valid URI"""
    try:
        result = encoding.iri_to_uri(iri)
        # Result should only contain ASCII characters
        assert all(ord(c) < 128 for c in result)
        # Result should be a string
        assert isinstance(result, str)
    except (UnicodeError, ValueError):
        # Some inputs might legitimately fail
        pass


# Test capfirst with empty strings and special cases
@given(st.text())
@example("")
@example(" ")
@example("123")
@example("émile")
def test_capfirst_edge_cases(s):
    """Test capfirst with various edge cases"""
    result = text.capfirst(s)
    
    if not s:
        assert result == s
    elif s[0].isalpha():
        assert result[0] == s[0].upper()
        if len(s) > 1:
            assert result[1:] == s[1:]
    else:
        # Non-alphabetic first character shouldn't change
        assert result == s