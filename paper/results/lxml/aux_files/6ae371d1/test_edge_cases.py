"""Test edge cases in text_compare wildcard handling"""

from hypothesis import given, strategies as st, assume
import lxml.doctestcompare as dc
import re

# Test for potential regex injection or escaping issues
@given(st.text())
def test_text_compare_regex_injection(text):
    """Ensure regex special characters in non-wildcard parts are properly escaped"""
    checker = dc.LXMLOutputChecker()
    
    # Test that literal text matches itself even with regex special chars
    # (as long as it doesn't contain the ... wildcard)
    assume('...' not in text)
    
    # Text should match itself
    assert checker.text_compare(text, text, True)
    
    # Text should NOT match with arbitrary replacements
    if text and not text.isspace():
        # Replace first char with 'X' - should not match
        modified = 'X' + text[1:] if len(text) > 1 else 'X'
        if modified != text:
            # Special chars like . or * should not act as regex
            if '.' in text:
                # A literal dot should not match any character
                assert not checker.text_compare(text, text.replace('.', 'X', 1), True)

# Test boundary conditions with escape sequences
@given(st.text())
def test_text_compare_escape_sequences(text):
    """Test that backslashes and escape sequences are handled correctly"""
    checker = dc.LXMLOutputChecker()
    
    # Create patterns with backslashes
    if '\\' not in text and '...' not in text:
        pattern = text + '\\n'
        target = text + '\\n'
        # Literal backslash-n should match
        assert checker.text_compare(pattern, target, True)
        # But not actual newline
        assert not checker.text_compare(pattern, text + '\n', True)

# Test for the specific edge case we thought was a bug
def test_dots_with_wildcard_edge_case():
    """Test the specific case of dots adjacent to wildcards"""
    checker = dc.LXMLOutputChecker()
    
    # These patterns work as designed:
    # '...' = wildcard
    # '....' = wildcard + literal dot
    # '.....' = wildcard + two literal dots
    # '......' = two wildcards
    
    test_cases = [
        # (pattern, text, should_match, description)
        ('...', 'anything', True, "Simple wildcard"),
        ('....', 'anything.', True, "Wildcard + literal dot"),
        ('.....', 'anything..', True, "Wildcard + two literal dots"), 
        ('......', 'anything', True, "Two wildcards"),
        ('...a...', 'Xa', True, "Two wildcards with letter between"),
        ('....a', 'X.a', True, "Wildcard + dot + a"),
        ('....a', 'Xa', False, "Wildcard + dot + a should NOT match without dot"),
    ]
    
    for pattern, text, should_match, desc in test_cases:
        result = checker.text_compare(pattern, text, True)
        print(f"{desc:40} | Pattern: {pattern:10} | Text: {text:15} | Expected: {should_match:5} | Got: {result:5} | {'✓' if result == should_match else '✗ MISMATCH'}")
        assert result == should_match, f"Failed: {desc}"

# Test normalization behavior
@given(st.text())
def test_norm_whitespace_preserves_content(text):
    """Test that norm_whitespace doesn't lose non-whitespace content"""
    normalized = dc.norm_whitespace(text)
    
    # All non-whitespace characters should be preserved
    original_non_ws = ''.join(c for c in text if not c.isspace())
    normalized_non_ws = ''.join(c for c in normalized if not c.isspace())
    assert original_non_ws == normalized_non_ws

# Test for potential issue with empty string handling
def test_empty_string_edge_cases():
    """Test edge cases with empty strings and None"""
    checker = dc.LXMLOutputChecker()
    
    # Test empty pattern matching
    assert checker.text_compare('', '', True)
    assert checker.text_compare(None, '', True) 
    assert checker.text_compare('', None, True)
    assert checker.text_compare(None, None, True)
    
    # Wildcard should match empty string
    assert checker.text_compare('...', '', True)
    
    print("All empty string tests passed ✓")

if __name__ == "__main__":
    print("Testing edge cases...")
    print("=" * 80)
    
    test_dots_with_wildcard_edge_case()
    print("\n" + "=" * 80)
    
    test_empty_string_edge_cases()
    print("\n" + "=" * 80)
    
    # Run hypothesis tests
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])