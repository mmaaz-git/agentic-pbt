#!/usr/bin/env python3
"""Additional edge case tests for sphinxcontrib.jsmath."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/sphinxcontrib-mermaid_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import re

# Test for potential edge cases in version parsing

@given(st.text())
def test_version_string_edge_cases(version_str):
    """Test version parsing with arbitrary strings."""
    try:
        # This is what the module does
        version_info = tuple(map(int, version_str.split('.')))
        
        # If it succeeds, verify properties
        assert isinstance(version_info, tuple)
        assert all(isinstance(x, int) for x in version_info)
        
        # Reconstruct and verify
        reconstructed = '.'.join(str(x) for x in version_info)
        parts = version_str.split('.')
        
        # Each part should be a valid integer string
        for i, part in enumerate(parts):
            assert str(int(part)) == str(version_info[i])
            
    except (ValueError, AttributeError):
        # Should fail for non-numeric parts
        parts = version_str.split('.')
        invalid = False
        for part in parts:
            if not part or not part.isdigit():
                invalid = True
                break
        assert invalid


@given(st.text(min_size=0, max_size=1000))
def test_empty_and_large_math_blocks(text):
    """Test edge cases for math block splitting."""
    parts = text.split('\n\n')
    
    # Empty string should give one empty part
    if text == '':
        assert parts == ['']
    
    # Single newline should not split
    if text == '\n':
        assert parts == ['\n']
    
    # Double newline should split into two empty strings
    if text == '\n\n':
        assert parts == ['', '']
    
    # Triple newline should have empty middle part
    if text == '\n\n\n':
        assert parts == ['', '\n']
    
    # Quadruple newline should split into three parts
    if text == '\n\n\n\n':
        assert parts == ['', '', '']


@given(st.integers(min_value=0, max_value=99999))
def test_version_number_limits(major):
    """Test version parsing with large numbers."""
    version_str = str(major)
    version_info = tuple(map(int, version_str.split('.')))
    assert version_info == (major,)
    
    # Test with multiple parts
    version_str2 = f"{major}.{major}.{major}"
    version_info2 = tuple(map(int, version_str2.split('.')))
    assert version_info2 == (major, major, major)


@given(st.text(alphabet='0123456789', min_size=1, max_size=100))
def test_version_with_leading_zeros(numeric_str):
    """Test version parsing with leading zeros."""
    # Create version with leading zeros
    version_str = f"0{numeric_str}.00{numeric_str}.{numeric_str}"
    
    try:
        version_info = tuple(map(int, version_str.split('.')))
        
        # Leading zeros should be stripped when converting to int
        expected = (int(f"0{numeric_str}"), int(f"00{numeric_str}"), int(numeric_str))
        assert version_info == expected
        
        # Verify integer conversion removes leading zeros
        assert version_info[0] == int(numeric_str)
        assert version_info[1] == int(numeric_str)
        assert version_info[2] == int(numeric_str)
    except ValueError:
        # Should not happen with numeric strings
        assert False, "Unexpected ValueError with numeric string"


@given(st.lists(st.text(min_size=0, max_size=10), min_size=0, max_size=10))
def test_math_block_join_split_invariant(text_parts):
    """Test that join and split are inverse operations."""
    joined = '\n\n'.join(text_parts)
    split_again = joined.split('\n\n')
    
    # Special case: empty list joins to empty string, which splits to ['']
    if text_parts == []:
        assert split_again == ['']
    else:
        # Should get back the original parts
        assert split_again == text_parts
    
    # Rejoin should give the same string
    rejoined = '\n\n'.join(split_again)
    assert rejoined == joined


@settings(max_examples=1000)
@given(st.text(alphabet='\\&', min_size=0, max_size=50))
def test_special_char_combinations(text):
    """Test various combinations of special characters."""
    has_amp = '&' in text
    has_backslash = '\\\\' in text
    
    # Count occurrences
    amp_count = text.count('&')
    backslash_pairs = text.count('\\\\')
    
    # Verify detection logic
    if amp_count > 0:
        assert has_amp
    if backslash_pairs > 0:
        assert has_backslash
    
    # Edge case: single backslash should not trigger
    if '\\' in text and '\\\\' not in text:
        assert not has_backslash
    
    # Multiple special chars
    if '&&&' in text:
        assert has_amp
        assert text.count('&') >= 3
    
    if '\\\\\\\\' in text:
        assert has_backslash
        assert text.count('\\\\') >= 2


if __name__ == '__main__':
    print("Running edge case tests...")
    
    print("\nTest 1: Version string edge cases...")
    test_version_string_edge_cases()
    
    print("Test 2: Empty and large math blocks...")
    test_empty_and_large_math_blocks()
    
    print("Test 3: Version number limits...")
    test_version_number_limits()
    
    print("Test 4: Version with leading zeros...")
    test_version_with_leading_zeros()
    
    print("Test 5: Math block join/split invariant...")
    test_math_block_join_split_invariant()
    
    print("Test 6: Special character combinations...")
    test_special_char_combinations()
    
    print("\nAll edge case tests completed!")