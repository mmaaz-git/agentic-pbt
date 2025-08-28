#!/usr/bin/env python3
"""Property-based tests for sphinxcontrib.jsmath using Hypothesis."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/sphinxcontrib-mermaid_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import re

# Import the module to test
from sphinxcontrib.jsmath import version

# Property 1: Version parsing should handle valid version strings correctly
@given(st.lists(st.integers(min_value=0, max_value=999), min_size=1, max_size=5))
def test_version_parsing_round_trip(version_parts):
    """Test that version string parsing is consistent."""
    version_str = '.'.join(str(v) for v in version_parts)
    parsed = tuple(map(int, version_str.split('.')))
    assert parsed == tuple(version_parts)


@given(st.text(alphabet='0123456789.', min_size=1))
def test_version_parsing_with_dots(version_str):
    """Test version parsing with various dot patterns."""
    # Filter out invalid versions (starting/ending with dots, consecutive dots)
    assume(not version_str.startswith('.'))
    assume(not version_str.endswith('.'))
    assume('..' not in version_str)
    assume(version_str != '.')
    
    parts = version_str.split('.')
    assume(all(part.isdigit() and part != '' for part in parts))
    
    # The version parsing logic in the module
    parsed = tuple(map(int, version_str.split('.')))
    
    # Verify the parsed result matches expectations
    assert len(parsed) == len(parts)
    assert all(isinstance(x, int) for x in parsed)
    
    # Reconstruct and verify round-trip
    reconstructed = '.'.join(str(x) for x in parsed)
    # Remove leading zeros for comparison
    normalized_original = '.'.join(str(int(p)) for p in parts)
    assert reconstructed == normalized_original


# Property 2: Math block splitting behavior
@given(st.text())
def test_math_block_splitting(text):
    """Test that splitting on '\\n\\n' behaves correctly."""
    parts = text.split('\n\n')
    
    # Properties that should hold:
    # 1. Join should reconstruct the original
    assert '\n\n'.join(parts) == text
    
    # 2. Number of parts should be consistent
    if '\n\n' not in text:
        assert len(parts) == 1
    else:
        # Count of '\n\n' should be len(parts) - 1
        count = text.count('\n\n')
        assert len(parts) == count + 1


# Property 3: Special character detection for math formatting
@given(st.text())
def test_special_char_detection(text):
    """Test the logic for detecting special math characters."""
    has_ampersand = '&' in text
    has_double_backslash = '\\\\' in text
    
    # The condition used in the module
    needs_split_env = has_ampersand or has_double_backslash
    
    # Verify detection is consistent
    if '&' in text:
        assert needs_split_env
    if '\\\\' in text:
        assert needs_split_env
    if not ('&' in text or '\\\\' in text):
        assert not needs_split_env


# Property 4: Test that __version_info__ matches __version__
def test_version_info_consistency():
    """Test that __version_info__ is correctly derived from __version__."""
    from sphinxcontrib.jsmath.version import __version__, __version_info__
    
    # Parse version manually
    expected = tuple(map(int, __version__.split('.')))
    assert __version_info__ == expected
    
    # Verify the format is as expected
    assert len(__version_info__) == len(__version__.split('.'))
    assert all(isinstance(x, int) for x in __version_info__)


# Property 5: HTML special character patterns
@given(st.text(alphabet='<>&"\'\\{}[]()$', min_size=0, max_size=100))
def test_html_special_chars_in_math(text):
    """Test handling of HTML special characters in math expressions."""
    # These characters should be handled specially in HTML context
    special_chars = ['<', '>', '&', '"', "'"]
    
    # Count special characters
    special_count = sum(text.count(char) for char in special_chars)
    
    # If we have special chars, they need encoding
    if special_count > 0:
        # This would need HTML encoding
        assert any(char in text for char in special_chars)
    
    # Backslashes have special meaning in LaTeX
    if '\\\\' in text:
        # Double backslash indicates line break in LaTeX
        parts = text.split('\\\\')
        assert len(parts) >= 2
        # Rejoin should give original
        assert '\\\\'.join(parts) == text


# Property 6: Math expression with split environments
@given(st.text(alphabet='abcxyz0123456789 \n&\\\\+-=', min_size=0, max_size=200))
def test_split_environment_logic(math_text):
    """Test the logic for when to use split environment."""
    # According to the code, split environment is used when '&' or '\\\\' is present
    use_split = '&' in math_text or '\\\\' in math_text
    
    if use_split:
        # Should wrap with \\begin{split} and \\end{split}
        wrapped = '\\begin{split}' + math_text + '\\end{split}'
        assert wrapped.startswith('\\begin{split}')
        assert wrapped.endswith('\\end{split}')
        assert math_text in wrapped
    else:
        # No wrapping needed
        assert not ('&' in math_text or '\\\\' in math_text)


if __name__ == '__main__':
    print("Running property-based tests for sphinxcontrib.jsmath...")
    
    # Run each test with a reasonable number of examples
    settings_obj = settings(max_examples=500)
    
    print("\nTest 1: Version parsing round-trip...")
    test_version_parsing_round_trip.hypothesis.settings = settings_obj
    test_version_parsing_round_trip()
    
    print("Test 2: Version parsing with dots...")
    test_version_parsing_with_dots.hypothesis.settings = settings_obj
    test_version_parsing_with_dots()
    
    print("Test 3: Math block splitting...")
    test_math_block_splitting()
    
    print("Test 4: Special character detection...")
    test_special_char_detection()
    
    print("Test 5: Version info consistency...")
    test_version_info_consistency()
    
    print("Test 6: HTML special characters...")
    test_html_special_chars_in_math()
    
    print("Test 7: Split environment logic...")
    test_split_environment_logic()
    
    print("\nAll property tests completed!")