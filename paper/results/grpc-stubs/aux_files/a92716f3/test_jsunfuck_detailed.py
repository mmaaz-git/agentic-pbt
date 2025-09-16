import sys
import os
sys.path.insert(0, '/root/hypothesis-llm/envs/cloudscraper_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings, example
import string

# Import the module we're testing
from cloudscraper.interpreters.jsunfuck import jsunfuck, MAPPING, SIMPLE, CONSTRUCTORS


# Test for potential bug: What if input contains both the pattern and its replacement?
@given(st.sampled_from(list(MAPPING.items())))
def test_jsunfuck_pattern_with_replacement(key_value_pair):
    """Test what happens when input contains both pattern and its replacement"""
    key, pattern = key_value_pair
    
    # Create input with both the pattern and what it would be replaced with
    test_input = f'{pattern}"{key}"{pattern}'
    
    result = jsunfuck(test_input)
    print(f"\nInput: {test_input[:100]}...")
    print(f"Result: {result[:100]}...")
    
    # Check what happened
    # The pattern should be replaced with "{key}"
    expected = f'"{key}""{key}""{key}"'
    assert result == expected


# Test for overlapping patterns
def test_overlapping_patterns():
    """Check if there are patterns that could interfere with each other"""
    overlaps = []
    
    for key1, pattern1 in MAPPING.items():
        for key2, pattern2 in MAPPING.items():
            if key1 != key2:
                if pattern1 in pattern2:
                    overlaps.append((key1, pattern1, key2, pattern2))
                    print(f"Pattern for '{key1}' is substring of pattern for '{key2}'")
    
    # If there are overlaps, the longer pattern must be replaced first
    # The code sorts by length (reverse=True), so this should be handled correctly
    if overlaps:
        print(f"Found {len(overlaps)} overlapping patterns")
        # Test that replacement order is correct
        for key1, pattern1, key2, pattern2 in overlaps:
            # pattern1 is substring of pattern2
            # If we have just pattern2, it should be replaced with "{key2}"
            result = jsunfuck(pattern2)
            assert result == f'"{key2}"', f"Longer pattern not replaced correctly: {pattern2[:50]}..."


# Test edge case: What if the replacement creates a new pattern?
def test_replacement_creates_pattern():
    """Test if a replacement could accidentally create a JSFuck pattern"""
    # This is a potential bug - if replacing pattern A creates pattern B
    
    # Check if any key when quoted could match another pattern
    for key in MAPPING.keys():
        quoted_key = f'"{key}"'
        for pattern in MAPPING.values():
            if pattern in quoted_key:
                print(f"WARNING: Quoted key '{key}' contains pattern: {pattern}")
                # This could cause issues!
                
    # Check SIMPLE replacements too
    for simple_key in SIMPLE.keys():
        for pattern in MAPPING.values():
            if pattern in simple_key:
                print(f"WARNING: Simple key '{simple_key}' contains MAPPING pattern: {pattern}")


# Test with very long strings
@given(st.integers(min_value=1, max_value=10))
def test_jsunfuck_repeated_patterns(repeat_count):
    """Test jsunfuck with repeated patterns"""
    # Take a pattern and repeat it many times
    pattern = MAPPING['a']  # '(false+"")[1]'
    
    # Create a string with the pattern repeated
    test_input = pattern * repeat_count
    result = jsunfuck(test_input)
    
    # Each pattern should be replaced
    expected = '"a"' * repeat_count
    assert result == expected, f"Failed with {repeat_count} repetitions"


# Test the actual order of operations
def test_replacement_order_detailed():
    """Verify that patterns are replaced in the correct order"""
    # Get all pattern lengths
    pattern_lengths = [(key, pattern, len(pattern)) for key, pattern in MAPPING.items()]
    pattern_lengths.sort(key=lambda x: x[2], reverse=True)
    
    # The first few longest patterns
    print("\nLongest patterns:")
    for key, pattern, length in pattern_lengths[:5]:
        print(f"  '{key}': {length} chars")
    
    # Create a test with multiple patterns of different lengths
    test_parts = []
    expected_parts = []
    
    # Use patterns of different lengths
    for i in [0, len(pattern_lengths)//2, len(pattern_lengths)-1]:
        key, pattern, _ = pattern_lengths[i]
        test_parts.append(pattern)
        expected_parts.append(f'"{key}"')
    
    test_input = '|'.join(test_parts)
    expected = '|'.join(expected_parts)
    
    result = jsunfuck(test_input)
    assert result == expected


# Test for infinite loop potential
@settings(max_examples=10, deadline=1000)  # Short deadline to catch infinite loops
@given(st.text(max_size=1000))
def test_no_infinite_loop(text):
    """Ensure jsunfuck doesn't get into infinite loops"""
    try:
        result = jsunfuck(text)
        # If we get here, no infinite loop
        assert isinstance(result, str)
    except Exception as e:
        # Check if it's a timeout (which would indicate infinite loop)
        assert 'deadline' not in str(e).lower(), f"Possible infinite loop detected: {e}"


# Specific test for the most complex patterns
def test_complex_patterns():
    """Test the most complex patterns in MAPPING"""
    # Test Infinity pattern specifically - it's very long
    infinity_pattern = SIMPLE['Infinity']
    test_input = f"prefix{infinity_pattern}suffix"
    result = jsunfuck(test_input)
    expected = "prefixInfinitysuffix"
    assert result == expected
    
    # Test patterns with special characters
    special_patterns = [
        ('"', MAPPING['"']),
        ('/', MAPPING['/']),
        ('=', MAPPING['=']),
    ]
    
    for key, pattern in special_patterns:
        test_input = pattern
        result = jsunfuck(test_input)
        expected = f'"{key}"'
        assert result == expected, f"Failed for special character '{key}'"


# Look for actual bugs: Empty string handling
def test_empty_and_whitespace():
    """Test edge cases with empty strings and whitespace"""
    test_cases = [
        ("", ""),  # Empty string
        (" ", " "),  # Single space
        ("\n", "\n"),  # Newline
        ("\t", "\t"),  # Tab
        ("   ", "   "),  # Multiple spaces
    ]
    
    for input_str, expected in test_cases:
        result = jsunfuck(input_str)
        assert result == expected, f"Failed for {repr(input_str)}"


# Test interaction between MAPPING and SIMPLE
def test_mapping_simple_interaction():
    """Test that MAPPING and SIMPLE replacements work together correctly"""
    # Create input with both MAPPING and SIMPLE patterns
    test_input = SIMPLE['false'] + MAPPING['a'] + SIMPLE['true']
    
    result = jsunfuck(test_input)
    # SIMPLE patterns should be replaced after MAPPING
    expected = 'false"a"true'
    assert result == expected