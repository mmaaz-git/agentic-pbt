"""Targeted tests to find real bugs in django.utils"""

from hypothesis import given, strategies as st, assume, example, settings
from django.utils import encoding, text, html, datastructures, http
import math


# Test 1: Look for edge cases in slugify that might produce invalid output
@given(st.text())
@example("--")
@example("__")  
@example("-_-_-")
@example("   -   ")
@example("\x00\x01\x02")  # Control characters
def test_slugify_produces_valid_slugs(s):
    """Slugify should always produce valid URL slugs or empty string"""
    result = text.slugify(s)
    
    # Empty result is valid
    if not result:
        return
        
    # Should not have consecutive hyphens (per the docstring: "Convert spaces or repeated dashes to single dashes")
    assert '--' not in result, f"Found consecutive dashes in: {result!r}"
    
    # Should match the pattern described in docstring
    import re
    assert re.match(r'^[a-z0-9]+(?:-[a-z0-9]+)*$', result), f"Invalid slug format: {result!r}"


# Test 2: MultiValueDict edge cases with None values
@given(st.text(min_size=1))
def test_multivalue_dict_none_handling(key):
    """Test how MultiValueDict handles None values"""
    mvd = datastructures.MultiValueDict()
    
    # Set a None value
    mvd[key] = None
    assert mvd.get(key) is None
    
    # setlist with None in the list
    mvd.setlist(key, [None, 'value', None])
    values = mvd.getlist(key)
    assert values == [None, 'value', None]


# Test 3: iri_to_uri with already-encoded URLs
@given(st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789%'))
def test_iri_to_uri_double_encoding(s):
    """Test that iri_to_uri handles already-encoded URLs correctly"""
    # Add a valid percent-encoded sequence
    test_input = s + '%20'
    
    result = encoding.iri_to_uri(test_input)
    
    # Check if it double-encodes the percent sign
    # If input has %20 (space), result should still have %20, not %2520
    if '%20' in test_input:
        # This might reveal double-encoding issues
        pass


# Test 4: compress_string with empty or very small inputs
@given(st.binary(max_size=10))
def test_compress_string_small_inputs(data):
    """Test compress_string with very small inputs"""
    import gzip
    
    compressed = text.compress_string(data)
    decompressed = gzip.decompress(compressed)
    
    # Should always be able to decompress
    assert decompressed == data
    
    # For very small inputs, compression might make it bigger
    # This is expected, but let's track the overhead
    if len(data) < 5:
        overhead = len(compressed) - len(data)
        # Just observe, don't assert - compression overhead is expected


# Test 5: format_html with special format strings
@given(
    st.text(),
    st.text()
)
def test_format_html_escaping(template, user_input):
    """Test that format_html properly escapes user input"""
    # Skip templates with actual format placeholders for now
    assume('{}' not in template and '{0}' not in template)
    
    try:
        # Try using the template as a format string with user input
        # This should escape the user_input
        result = html.format_html("{}", user_input)
        
        # User input should be escaped
        if '<' in user_input:
            assert '&lt;' in str(result)
        if '>' in user_input:
            assert '&gt;' in str(result)
        if '&' in user_input and not user_input.startswith('&'):
            # Check that standalone & is escaped
            pass
    except (ValueError, IndexError, KeyError):
        # Some format strings might be invalid
        pass


# Test 6: OrderedSet operations
@given(
    st.lists(st.integers(), min_size=1),
    st.lists(st.integers(), min_size=1)
)
def test_ordered_set_operations(list1, list2):
    """Test OrderedSet set operations preserve order of first operand"""
    os1 = datastructures.OrderedSet(list1)
    os2 = datastructures.OrderedSet(list2)
    
    # Union should preserve order of first set
    union = os1 | os2
    
    # Check that all elements from os1 appear in the same order
    os1_elements = list(os1)
    union_list = list(union)
    
    # Filter union_list to only elements from os1
    os1_in_union = [x for x in union_list if x in os1]
    
    # These should be in the same order
    assert os1_in_union == os1_elements


# Test 7: escape_uri_path with unicode characters
@given(st.text())
def test_escape_uri_path_unicode(path):
    """Test escape_uri_path handles unicode correctly"""
    try:
        result = encoding.escape_uri_path(path)
        
        # Result should be ASCII-safe for URI
        assert all(ord(c) < 128 or c == '%' for c in result)
        
        # Spaces should be encoded as %20
        if ' ' in path:
            assert '%20' in result
            
    except (UnicodeError, ValueError) as e:
        # Some inputs might fail - that's worth investigating
        if len(path) < 100:  # Only print for reasonable sized inputs
            print(f"escape_uri_path failed on: {path!r}")
            raise


# Test 8: DictWrapper behavior
@given(
    st.dictionaries(st.text(min_size=1), st.integers()),
    st.text(min_size=1)
)
def test_dict_wrapper_prefix(data, prefix):
    """Test DictWrapper with prefix functionality"""
    
    def get_value(key):
        return data.get(key, "DEFAULT")
    
    wrapper = datastructures.DictWrapper(get_value, prefix)
    
    # Accessing a key should call get_value with prefix + key
    for key in data:
        full_key = prefix + key
        if full_key in data:
            # This reveals how DictWrapper actually works
            pass


# Test 9: Multiple HTML escaping (potential double-escape issue)
@given(st.text())
def test_html_escape_idempotence(s):
    """Test if HTML escape is idempotent or not"""
    once = html.escape(s)
    twice = html.escape(once)
    
    # According to the docstring, escape "Always escapes input, even if it's already escaped"
    # So twice should have double-escaping
    if '&' in s:
        # If original has &, once will have &amp;, twice will have &amp;amp;
        assert str(twice) != str(once)
        # This is documented behavior, not a bug


# Test 10: CaseInsensitiveMapping edge cases
@given(st.text(min_size=1))
@example("ß")  # German sharp s
@example("İ")  # Turkish capital I with dot
@example("ı")  # Turkish lowercase i without dot
def test_case_insensitive_mapping_unicode_edge_cases(key):
    """Test CaseInsensitiveMapping with Unicode edge cases"""
    ci_map = datastructures.CaseInsensitiveMapping({key: "value"})
    
    # Basic case-insensitive access
    assert ci_map.get(key) == "value"
    assert ci_map.get(key.upper()) == "value"
    assert ci_map.get(key.lower()) == "value"
    
    # Check special Unicode cases
    # Turkish I problem: İ.lower() = 'i̇' and ı.upper() = 'I'
    # German ß: ß.upper() = 'SS'
    if key == 'ß':
        # This is an interesting edge case
        # ß.upper() is 'SS', but 'SS'.lower() is 'ss', not 'ß'
        assert ci_map.get('SS') == "value"  # Should this work?
        assert ci_map.get('ss') == "value"
        assert ci_map.get('Ss') == "value"