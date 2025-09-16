"""Test edge cases in assertOutputMatches regex handling."""

import sys
import re
from hypothesis import given, strategies as st, assume
import fire.testutils


# Test special regex characters in output
@given(
    special_chars=st.sampled_from(['(', ')', '[', ']', '{', '}', '*', '+', '?', '.', '^', '$', '|', '\\']),
    count=st.integers(min_value=1, max_value=5)
)
def test_regex_special_chars_in_output(special_chars, count):
    """Test that special regex characters in output are handled correctly."""
    
    test_case = fire.testutils.BaseTestCase()
    test_case.setUp()
    
    # Create output with special characters
    output_text = special_chars * count
    
    # Test with pattern that should match anything
    with test_case.assertOutputMatches(stdout='.*', stderr='.*'):
        sys.stdout.write(output_text)
        sys.stderr.write(output_text)
    
    # Test with None pattern and empty output
    with test_case.assertOutputMatches(stdout=None, stderr=None):
        sys.stdout.write('')
        sys.stderr.write('')


# Test multiline and DOTALL behavior
@given(
    lines=st.lists(st.text(min_size=1, max_size=10), min_size=2, max_size=5)
)
def test_multiline_dotall_behavior(lines):
    """Test that DOTALL and MULTILINE flags work as expected."""
    
    test_case = fire.testutils.BaseTestCase()
    test_case.setUp()
    
    # Create multiline output
    output = '\n'.join(lines)
    
    # Pattern that should match across lines with DOTALL
    pattern = '.*'
    
    with test_case.assertOutputMatches(stdout=pattern):
        sys.stdout.write(output)
    
    # Test that . matches newlines (DOTALL is enabled)
    if len(lines) > 1:
        # Create a pattern that spans lines
        first_word = lines[0][:3] if len(lines[0]) >= 3 else lines[0]
        last_word = lines[-1][-3:] if len(lines[-1]) >= 3 else lines[-1]
        
        # Skip if either word contains regex special chars
        try:
            re.compile(first_word)
            re.compile(last_word)
        except re.error:
            assume(False)
        
        # This pattern should match because DOTALL is enabled
        cross_line_pattern = f"{re.escape(first_word)}.*{re.escape(last_word)}"
        
        with test_case.assertOutputMatches(stdout=cross_line_pattern):
            sys.stdout.write(output)


# Test empty string edge cases
def test_empty_string_patterns():
    """Test edge cases with empty patterns and outputs."""
    
    test_case = fire.testutils.BaseTestCase()
    test_case.setUp()
    
    # Empty pattern should match empty output
    with test_case.assertOutputMatches(stdout='', stderr=''):
        sys.stdout.write('')
        sys.stderr.write('')
    
    # Empty pattern should also match non-empty output (matches at position 0)
    with test_case.assertOutputMatches(stdout='', stderr=''):
        sys.stdout.write('hello')
        sys.stderr.write('world')


# Test very long output
@given(
    char=st.characters(min_codepoint=65, max_codepoint=90),
    length=st.integers(min_value=10000, max_value=50000)
)
def test_long_output_performance(char, length):
    """Test that assertOutputMatches handles very long output efficiently."""
    
    test_case = fire.testutils.BaseTestCase()
    test_case.setUp()
    
    # Create very long output
    long_output = char * length
    
    # Should handle this without issues
    with test_case.assertOutputMatches(stdout='.*'):
        sys.stdout.write(long_output)


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short", "-x"])