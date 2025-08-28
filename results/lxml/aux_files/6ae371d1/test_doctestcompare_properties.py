"""Property-based tests for lxml.doctestcompare module"""

import re
from hypothesis import given, strategies as st, assume, settings
import lxml.doctestcompare as dc

# Test idempotence property of norm_whitespace
@given(st.text())
def test_norm_whitespace_idempotent(s):
    """Applying norm_whitespace twice should be the same as once"""
    once = dc.norm_whitespace(s)
    twice = dc.norm_whitespace(once)
    assert once == twice

# Test strip handles None correctly
@given(st.one_of(st.none(), st.text()))
def test_strip_none_handling(value):
    """strip should handle None correctly"""
    result = dc.strip(value)
    if value is None:
        assert result is None
    else:
        assert result == value.strip()

# Test format_text HTML escaping round-trip with unescaping
@given(st.text())
def test_format_text_escaping(text):
    """format_text should properly escape HTML characters"""
    checker = dc.LXMLOutputChecker()
    result = checker.format_text(text)
    
    # Check that HTML special chars are escaped
    if text and text.strip():  # Only if non-empty after stripping
        if '<' in text:
            assert '&lt;' in result
        if '>' in text:
            assert '&gt;' in result
        if '&' in text and not re.search(r'&(?:lt|gt|amp|quot);', text):
            assert '&amp;' in result
        if '"' in text:
            assert '&quot;' in result

# Test text_compare wildcard behavior
@given(st.text(), st.text(), st.text())
def test_text_compare_wildcard(prefix, suffix, middle):
    """Test that ... wildcard matches any text in between"""
    checker = dc.LXMLOutputChecker()
    
    # Build a pattern with wildcard
    pattern = prefix + "..." + suffix
    
    # Build text that should match
    text = prefix + middle + suffix
    
    # The pattern should match the text
    assert checker.text_compare(pattern, text, True)

# Test text_compare edge cases with empty strings
@given(st.one_of(st.none(), st.just(''), st.text()))
def test_text_compare_empty_handling(want):
    """Test text_compare handles empty/None correctly"""
    checker = dc.LXMLOutputChecker()
    
    # Empty or None should match empty string
    if want is None or want == '':
        assert checker.text_compare(want, '', True)
        assert checker.text_compare(want, None, True)

# Test tag_compare namespace ellipsis
@given(st.text(min_size=1), st.text(min_size=1))
def test_tag_compare_namespace_ellipsis(namespace, tagname):
    """Test that {..} namespace ellipsis matches any namespace"""
    assume('}' not in namespace and '{' not in namespace)
    assume('}' not in tagname and '{' not in tagname)
    
    checker = dc.LXMLOutputChecker()
    
    # {..}tagname should match {anything}tagname
    pattern = '{...}' + tagname
    actual = '{' + namespace + '}' + tagname
    
    assert checker.tag_compare(pattern, actual)
    
    # But should also match plain tagname
    assert checker.tag_compare(pattern, tagname)

# Test tag_compare with 'any' wildcard
@given(st.text())
def test_tag_compare_any_wildcard(tagname):
    """Test that 'any' tag matches any tag"""
    checker = dc.LXMLOutputChecker()
    assert checker.tag_compare('any', tagname)

# Test multiple ... replacements in text_compare
@given(st.lists(st.text(min_size=1, max_size=5, alphabet='abcABC0123 '), min_size=2, max_size=5))
def test_text_compare_multiple_wildcards(parts):
    """Test multiple ... wildcards in a pattern"""
    checker = dc.LXMLOutputChecker()
    
    # Create pattern with wildcards between parts (avoiding dots in parts)
    pattern = '...'.join(parts)
    
    # Create text with extra content between parts
    text_parts = []
    for i, part in enumerate(parts):
        text_parts.append(part)
        if i < len(parts) - 1:
            text_parts.append('extra_content')
    text = ''.join(text_parts)
    
    # Pattern should match
    assert checker.text_compare(pattern, text, True)

# Test collect_diff_text behavior
@given(st.text(), st.text())
def test_collect_diff_text_consistency(want, got):
    """Test collect_diff_text returns consistent format"""
    checker = dc.LXMLOutputChecker()
    result = checker.collect_diff_text(want, got, strip=True)
    
    # Result should be a string
    assert isinstance(result, str)
    
    # If text matches, it should return the formatted got text
    if checker.text_compare(want, got, strip=True):
        if got:
            assert result == checker.format_text(got, strip=True)
        else:
            assert result == ''

# Test format_text with strip parameter
@given(st.text())
def test_format_text_strip_parameter(text):
    """Test format_text respects the strip parameter"""
    checker = dc.LXMLOutputChecker()
    
    # With strip=True (default)
    stripped_result = checker.format_text(text, strip=True)
    
    # With strip=False
    unstripped_result = checker.format_text(text, strip=False)
    
    # If text has leading/trailing whitespace, results should differ
    if text and (text[0].isspace() or text[-1].isspace()):
        # When stripped, shouldn't have leading/trailing whitespace
        if stripped_result:
            assert not stripped_result[0].isspace() and not stripped_result[-1].isspace()
    
    # HTML escaping should still happen in both cases
    if '<' in text:
        assert '&lt;' in stripped_result or stripped_result == ''
        assert '&lt;' in unstripped_result

# Edge case: Test text_compare with regex special characters
@given(st.text(alphabet='.^$*+?{}[]\\|()', min_size=1, max_size=10))
def test_text_compare_regex_special_chars(text):
    """Test text_compare handles regex special characters correctly"""
    checker = dc.LXMLOutputChecker()
    
    # Text with regex special chars should match itself
    assert checker.text_compare(text, text, True)
    
    # But shouldn't match as regex pattern
    if '.' in text and text != '.':
        # A literal dot shouldn't match any character
        assert not checker.text_compare(text, text.replace('.', 'X'), True)

if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])