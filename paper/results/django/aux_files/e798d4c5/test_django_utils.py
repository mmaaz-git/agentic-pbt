"""Property-based tests for django.utils using Hypothesis"""

import re
from hypothesis import given, strategies as st, assume, settings
from django.utils import encoding, text, html, datastructures


# Test 1: encoding.force_str/force_bytes round-trip property
@given(st.text())
def test_force_str_bytes_roundtrip(s):
    """Test that force_str(force_bytes(x)) preserves the data"""
    # Convert string to bytes and back
    as_bytes = encoding.force_bytes(s)
    back_to_str = encoding.force_str(as_bytes)
    assert back_to_str == s


# Test 2: text.slugify idempotence
@given(st.text())
def test_slugify_idempotent(s):
    """Test that slugify(slugify(x)) == slugify(x) - idempotence property"""
    slugified_once = text.slugify(s)
    slugified_twice = text.slugify(slugified_once)
    assert slugified_once == slugified_twice


# Test 3: text.slugify with allow_unicode idempotence
@given(st.text())
def test_slugify_unicode_idempotent(s):
    """Test slugify idempotence with allow_unicode=True"""
    slugified_once = text.slugify(s, allow_unicode=True)
    slugified_twice = text.slugify(slugified_once, allow_unicode=True)
    assert slugified_once == slugified_twice


# Test 4: text.capfirst invariant - only first char should change
@given(st.text(min_size=2))
def test_capfirst_only_first_char(s):
    """Test that capfirst only modifies the first character"""
    result = text.capfirst(s)
    # The rest of the string (after first char) should be unchanged
    if len(s) > 1:
        assert result[1:] == s[1:]
    # First char should be uppercase if it's a letter
    if s and s[0].isalpha():
        assert result[0] == s[0].upper()


# Test 5: MultiValueDict setlist/getlist round-trip
@given(
    st.text(min_size=1),  # key
    st.lists(st.text(), min_size=1)  # list of values
)
def test_multivalue_dict_roundtrip(key, values):
    """Test that setlist/getlist are inverse operations"""
    mvd = datastructures.MultiValueDict()
    mvd.setlist(key, values)
    retrieved = mvd.getlist(key)
    assert retrieved == values


# Test 6: html.escape safety - all dangerous chars should be escaped
@given(st.text())
def test_html_escape_safety(s):
    """Test that html.escape escapes all dangerous HTML characters"""
    escaped = html.escape(s)
    # Check that dangerous characters are escaped
    assert '<' not in str(escaped)
    assert '>' not in str(escaped)
    assert '&' not in str(escaped) or '&amp;' in str(escaped) or '&lt;' in str(escaped) or '&gt;' in str(escaped) or '&quot;' in str(escaped) or '&#x27;' in str(escaped)
    assert '"' not in str(escaped) or '&quot;' in str(escaped)


# Test 7: text.slugify output format invariant
@given(st.text())
def test_slugify_output_format(s):
    """Test that slugify output only contains allowed characters"""
    result = text.slugify(s, allow_unicode=False)
    # According to docstring: only alphanumerics, underscores, or hyphens
    # Also converts to lowercase
    if result:  # Empty string is valid
        assert re.match(r'^[a-z0-9_-]+$', result), f"Invalid characters in slugify output: {result}"
        # No leading/trailing dashes or underscores (per docstring)
        assert not result.startswith('-')
        assert not result.startswith('_')
        assert not result.endswith('-')
        assert not result.endswith('_')


# Test 8: iri_to_uri preserves ASCII characters
@given(st.text(alphabet=st.characters(min_codepoint=32, max_codepoint=126)))
def test_iri_to_uri_preserves_ascii(s):
    """Test that iri_to_uri preserves most ASCII characters"""
    # Skip if it contains percent signs which might be interpreted as already encoded
    assume('%' not in s)
    result = encoding.iri_to_uri(s)
    # Most ASCII chars should be preserved (except space which becomes %20)
    for char in s:
        if char == ' ':
            assert '%20' in result
        elif char.isalnum() or char in '-_.~/':
            assert char in result


# Test 9: OrderedSet maintains set invariants
@given(st.lists(st.integers()))
def test_ordered_set_uniqueness(items):
    """Test that OrderedSet maintains uniqueness while preserving order"""
    ordered_set = datastructures.OrderedSet(items)
    # Should have no duplicates
    assert len(ordered_set) == len(set(items))
    # Should preserve first occurrence order
    seen = set()
    expected = []
    for item in items:
        if item not in seen:
            seen.add(item)
            expected.append(item)
    assert list(ordered_set) == expected


# Test 10: CaseInsensitiveMapping property
@given(
    st.dictionaries(
        st.text(alphabet=st.characters(min_codepoint=65, max_codepoint=122), min_size=1),
        st.text()
    )
)
def test_case_insensitive_mapping(data):
    """Test that CaseInsensitiveMapping is truly case-insensitive"""
    ci_map = datastructures.CaseInsensitiveMapping(data)
    for key, value in data.items():
        # Should be able to access with any case variation
        assert ci_map.get(key.lower()) == value
        assert ci_map.get(key.upper()) == value
        if key.lower() in ci_map:
            assert key.upper() in ci_map