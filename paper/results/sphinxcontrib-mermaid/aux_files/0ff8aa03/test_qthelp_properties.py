"""Property-based tests for sphinxcontrib.qthelp functions."""

import re
import html
from hypothesis import given, strategies as st, assume, settings
import pytest

# Import our extracted functions
from qthelp_module import (
    escape_for_xml,
    normalize_namespace,
    split_index_entry,
    merge_keywords,
    build_section_xml,
    build_keyword_xml,
    _idpattern
)


# Test 1: normalize_namespace should always produce valid normalized namespaces
@given(st.text())
def test_normalize_namespace_invariants(namespace):
    """Test that normalize_namespace always produces valid output."""
    result = normalize_namespace(namespace)
    
    # Property 1: Result should always start with 'org.sphinx.'
    assert result.startswith('org.sphinx.'), f"Namespace '{result}' doesn't start with 'org.sphinx.'"
    
    # Property 2: Result should only contain alphanumeric characters and dots
    assert re.match(r'^[a-zA-Z0-9.]+$', result), f"Namespace '{result}' contains invalid characters"
    
    # Property 3: Idempotence - normalizing twice should give same result
    assert normalize_namespace(result) == result, "normalize_namespace is not idempotent"


# Test 2: escape_for_xml should properly escape dangerous XML characters
@given(st.text())
def test_escape_for_xml_safety(text):
    """Test that escape_for_xml properly escapes dangerous characters."""
    result = escape_for_xml(text)
    
    # Check that the original dangerous characters have been escaped
    if '<' in text:
        assert '&lt;' in result, f"'<' not properly escaped in result: {result}"
    if '>' in text:
        assert '&gt;' in result, f"'>' not properly escaped in result: {result}"
    if '"' in text:
        assert '&quot;' in result, f"'\"' not properly escaped in result: {result}"
    if '&' in text:
        # Original & should be escaped to &amp;
        # Count how many & were in original vs result
        original_amp_count = text.count('&')
        # Each original & becomes &amp; (so adds 4 chars per &)
        # But < becomes &lt; (adds an &), > becomes &gt; (adds an &), " becomes &quot; (adds an &)
        # This is complex, so just verify &amp; appears if & was in original
        assert '&amp;' in result or any(x in result for x in ['&lt;', '&gt;', '&quot;']), \
            f"'&' not properly handled in result: {result}"
    
    # Property: Escaping should be deterministic
    assert escape_for_xml(text) == escape_for_xml(text), "escape_for_xml is not deterministic"


# Test 3: Round-trip property for escape_for_xml
@given(st.text())
def test_escape_unescape_roundtrip(text):
    """Test that escaping and unescaping is a round-trip operation."""
    escaped = escape_for_xml(text)
    unescaped = html.unescape(escaped)
    
    # Property: Round-trip should preserve original text
    assert unescaped == text, f"Round-trip failed: '{text}' -> '{escaped}' -> '{unescaped}'"


# Test 4: merge_keywords should maintain uniqueness
@given(
    st.lists(st.tuples(st.text(), st.text(), st.text())),
    st.lists(st.tuples(st.text(), st.text(), st.text()))
)
def test_merge_keywords_uniqueness(keywords1, keywords2):
    """Test that merge_keywords removes duplicates."""
    result = merge_keywords(keywords1, keywords2)
    
    # Property 1: Result should have no duplicates
    assert len(result) == len(set(result)), "merge_keywords produced duplicates"
    
    # Property 2: All original unique keywords should be in result
    unique_input = list(set(keywords1 + keywords2))
    assert set(result) == set(unique_input), "merge_keywords lost or added keywords"
    
    # Property 3: Order should be preserved for first occurrences
    seen = set()
    expected_order = []
    for kw in keywords1 + keywords2:
        if kw not in seen:
            seen.add(kw)
            expected_order.append(kw)
    assert result == expected_order, "merge_keywords didn't preserve order"


# Test 5: merge_keywords idempotence
@given(st.lists(st.tuples(st.text(), st.text(), st.text())))
def test_merge_keywords_idempotent(keywords):
    """Test that merging with empty list is identity operation."""
    # Property: Merging with empty list should return same list (without duplicates)
    result = merge_keywords(keywords, [])
    expected = merge_keywords(keywords, keywords)  # This removes duplicates
    
    # The result of merging with empty should be same as deduplicating the list
    seen = set()
    deduplicated = []
    for kw in keywords:
        if kw not in seen:
            seen.add(kw)
            deduplicated.append(kw)
    
    assert result == deduplicated, "merge_keywords with empty list is not identity"


# Test 6: split_index_entry pattern matching
@given(st.text())
def test_split_index_entry_consistency(entry):
    """Test split_index_entry produces consistent results."""
    title, id_part = split_index_entry(entry)
    
    # Property 1: If no pattern match, title should be the whole entry and id should be None
    if not _idpattern.match(entry):
        assert title == entry, f"Non-matching entry should return full text as title"
        assert id_part is None, f"Non-matching entry should return None as id"
    
    # Property 2: If pattern matches, title and id should be extracted correctly
    if _idpattern.match(entry):
        assert title is not None, "Matching entry should have a title"
        # Reconstruct and verify (approximately - the pattern is complex)
        if id_part:
            assert id_part in entry, f"Extracted id '{id_part}' not found in original entry"


# Test 7: Valid index entries should be split correctly
@given(
    title=st.text(min_size=1).filter(lambda x: '(' not in x and ')' not in x),
    id_part=st.from_regex(r'[a-zA-Z_][a-zA-Z0-9_.]*', fullmatch=True)
)
def test_split_index_entry_valid_patterns(title, id_part):
    """Test that valid index entries are split correctly."""
    # Create a valid entry
    entry = f"{title} ({id_part})"
    
    result_title, result_id = split_index_entry(entry)
    
    # Property: Valid patterns should be parsed correctly
    assert result_title == title, f"Title mismatch: expected '{title}', got '{result_title}'"
    assert result_id == id_part, f"ID mismatch: expected '{id_part}', got '{result_id}'"


# Test 8: build_section_xml should produce valid XML
@given(
    title=st.text(),
    ref=st.text(),
    indent=st.integers(min_value=0, max_value=10)
)
def test_build_section_xml_validity(title, ref, indent):
    """Test that build_section_xml produces valid XML elements."""
    result = build_section_xml(title, ref, indent)
    
    # Property 1: Result should contain proper indentation
    expected_spaces = ' ' * (4 * indent)
    assert result.startswith(expected_spaces), f"Incorrect indentation"
    
    # Property 2: Result should be a valid section element
    assert '<section' in result, "Missing section element"
    assert 'title=' in result, "Missing title attribute"
    assert 'ref=' in result, "Missing ref attribute"
    assert result.strip().endswith('/>'), "Section element not properly closed"
    
    # Property 3: Dangerous characters should be escaped
    if '<' in title or '>' in title or '"' in title or '&' in title:
        # These should have been escaped
        content_part = result[len(expected_spaces):]
        # Extract the attribute values
        import re
        title_match = re.search(r'title="([^"]*)"', content_part)
        if title_match:
            extracted_title = title_match.group(1)
            # The extracted title should be escaped version
            assert extracted_title == html.escape(title, quote=True), \
                f"Title not properly escaped in XML"


# Test 9: build_keyword_xml should produce valid XML  
@given(
    keyword=st.text(),
    id_val=st.text(),
    ref=st.text(),
    indent=st.integers(min_value=0, max_value=10)
)
def test_build_keyword_xml_validity(keyword, id_val, ref, indent):
    """Test that build_keyword_xml produces valid XML elements."""
    result = build_keyword_xml(keyword, id_val, ref, indent)
    
    # Property 1: Result should contain proper indentation
    expected_spaces = ' ' * (4 * indent)
    assert result.startswith(expected_spaces), f"Incorrect indentation"
    
    # Property 2: Result should be a valid keyword element
    assert '<keyword' in result, "Missing keyword element"
    assert 'name=' in result, "Missing name attribute"
    assert 'id=' in result, "Missing id attribute"
    assert 'ref=' in result, "Missing ref attribute"
    assert result.strip().endswith('/>'), "Keyword element not properly closed"
    
    # Property 3: All attributes should be properly escaped
    if any(c in keyword + id_val + ref for c in ['<', '>', '"', '&']):
        # Verify escaping by checking no raw dangerous characters in attributes
        content_part = result[len(expected_spaces):]
        # Should not have unescaped quotes inside attribute values
        assert content_part.count('"') % 2 == 0, "Unmatched quotes, likely unescaped"


# Test 10: Stress test with malicious inputs
@given(st.text().map(lambda x: x + '<script>alert("XSS")</script>'))
def test_xml_builders_xss_protection(malicious_input):
    """Test that XML builders properly escape malicious inputs."""
    # Test build_section_xml
    section = build_section_xml(malicious_input, malicious_input)
    assert '<script>' not in section, "Unescaped script tag in section XML"
    assert 'alert(' not in section or '&' in section, "Unescaped JavaScript in section XML"
    
    # Test build_keyword_xml
    keyword = build_keyword_xml(malicious_input, malicious_input, malicious_input)
    assert '<script>' not in keyword, "Unescaped script tag in keyword XML"
    assert 'alert(' not in keyword or '&' in keyword, "Unescaped JavaScript in keyword XML"