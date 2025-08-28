import sys
import os
sys.path.insert(0, '/root/hypothesis-llm/envs/cloudscraper_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import string
import re

# Import the module we're testing
from cloudscraper.interpreters.jsunfuck import jsunfuck, MAPPING, SIMPLE, CONSTRUCTORS


# Test 1: jsunfuck should be idempotent
@given(st.text())
def test_jsunfuck_idempotence(input_string):
    """Running jsunfuck twice should give the same result as running it once"""
    once = jsunfuck(input_string)
    twice = jsunfuck(once)
    assert once == twice, f"jsunfuck is not idempotent for input: {repr(input_string[:100])}"


# Test 2: jsunfuck should preserve strings without JSFuck patterns
@given(st.text(alphabet=string.ascii_letters + string.digits + " \t\n", min_size=1))
def test_jsunfuck_preserves_normal_text(input_string):
    """Strings without JSFuck patterns should remain unchanged"""
    # Skip if the string accidentally contains JSFuck patterns
    for pattern in MAPPING.values():
        if pattern in input_string:
            assume(False)
    for pattern in SIMPLE.values():
        if pattern in input_string:
            assume(False)
    
    result = jsunfuck(input_string)
    assert result == input_string, f"jsunfuck modified a string without JSFuck patterns"


# Test 3: Mapping consistency - no infinite loops
def test_mapping_consistency():
    """No mapping key should appear in its replacement value to avoid infinite loops"""
    for key, value in MAPPING.items():
        # The replacement is '"{}"'.format(key), so check if key appears in the formatted result
        replacement = '"{}"'.format(key)
        # This is actually checking if applying the mapping could create an infinite loop
        assert value not in replacement, f"Mapping for {repr(key)} could cause issues: {repr(value)} -> {repr(replacement)}"


# Test 4: jsunfuck with actual JSFuck patterns
@given(st.sampled_from(list(MAPPING.values())))
def test_jsunfuck_replaces_known_patterns(pattern):
    """jsunfuck should replace known JSFuck patterns"""
    # Find which key this pattern maps to
    key = [k for k, v in MAPPING.items() if v == pattern][0]
    
    # Create a test string with the pattern
    test_string = f"prefix{pattern}suffix"
    result = jsunfuck(test_string)
    
    # The pattern should be replaced with the quoted key
    expected = f'prefix"{key}"suffix'
    assert result == expected, f"Failed to replace pattern {repr(pattern)} with {repr(key)}"


# Test 5: Order of replacement shouldn't matter for non-overlapping patterns
@given(
    st.lists(st.sampled_from(list(MAPPING.values())), min_size=2, max_size=5, unique=True),
    st.text(alphabet=string.ascii_letters, max_size=10)
)
def test_jsunfuck_multiple_patterns(patterns, separator):
    """Multiple non-overlapping patterns should all be replaced correctly"""
    # Build a string with multiple patterns separated
    test_parts = []
    expected_parts = []
    
    for pattern in patterns:
        key = [k for k, v in MAPPING.items() if v == pattern][0]
        test_parts.append(pattern)
        expected_parts.append(f'"{key}"')
    
    # Join with separator to ensure patterns don't overlap
    test_string = separator.join(test_parts)
    expected = separator.join(expected_parts)
    
    result = jsunfuck(test_string)
    assert result == expected, f"Failed to replace multiple patterns correctly"


# Test 6: Check for potential replacement order issues
def test_replacement_order_matters():
    """Test that longer patterns are replaced before shorter ones"""
    # This is important because the function sorts by length (reverse=True)
    # Create a scenario where order matters
    
    # If we have patterns where one is a substring of another, 
    # we need to replace the longer one first
    
    # Look for such cases in MAPPING
    for key1, pattern1 in MAPPING.items():
        for key2, pattern2 in MAPPING.items():
            if key1 != key2 and pattern1 != pattern2:
                if pattern1 in pattern2:
                    # pattern2 contains pattern1, so pattern2 should be replaced first
                    test_string = pattern2
                    result = jsunfuck(test_string)
                    
                    # The longer pattern should be replaced, not the shorter one
                    expected = f'"{key2}"'
                    assert result == expected, f"Replacement order issue: {pattern2} should be replaced with {key2}, not partially replaced"


# Test 7: Edge cases with empty strings and special characters
@given(st.one_of(
    st.just(""),
    st.just(" "),
    st.just("\n"),
    st.just("\t"),
    st.text(alphabet="[](){}!+", max_size=20)
))
def test_jsunfuck_edge_cases(input_string):
    """jsunfuck should handle edge cases gracefully"""
    try:
        result = jsunfuck(input_string)
        # Should not raise an exception
        assert isinstance(result, str)
        
        # Idempotence should still hold
        twice = jsunfuck(result)
        assert result == twice
    except Exception as e:
        assert False, f"jsunfuck raised exception on edge case {repr(input_string)}: {e}"