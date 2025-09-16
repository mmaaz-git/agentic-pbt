"""Test for round-trip bug in concatenate/split functions"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/djangorestframework-api-key_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, settings, HealthCheck


# Direct test for the round-trip bug
def test_round_trip_bug_example():
    """Demonstrate that concatenate/split violates round-trip when left contains dots"""
    from rest_framework_api_key.crypto import concatenate, split
    
    # If left contains a dot, the round-trip property is violated
    left = "prefix.with.dots"
    right = "secret_key"
    
    concatenated = concatenate(left, right)
    print(f"Original left: {left}")
    print(f"Original right: {right}")
    print(f"Concatenated: {concatenated}")
    
    result_left, result_right = split(concatenated)
    print(f"Result left: {result_left}")
    print(f"Result right: {result_right}")
    
    # This assertion will FAIL - demonstrating the bug!
    assert result_left == left, f"Round-trip failed: expected '{left}', got '{result_left}'"
    assert result_right == right, f"Round-trip failed: expected '{right}', got '{result_right}'"


# Property test with better strategy
@given(
    left=st.text(alphabet=st.characters(min_codepoint=33, blacklist_characters='.'), min_size=1, max_size=20),
    dots_in_left=st.integers(min_value=1, max_value=3),
    right=st.text(min_size=1, max_size=20)
)
@settings(suppress_health_check=[HealthCheck.filter_too_much], max_examples=100)
def test_round_trip_violation_with_dots(left, dots_in_left, right):
    """Test that dots in left part break the round-trip property"""
    from rest_framework_api_key.crypto import concatenate, split
    
    # Add dots to the left part
    left_parts = [left[i:i+len(left)//dots_in_left] for i in range(0, len(left), max(1, len(left)//dots_in_left))]
    left_with_dots = ".".join(filter(None, left_parts))
    
    if not left_with_dots:  # Skip if we ended up with empty string
        return
    
    concatenated = concatenate(left_with_dots, right)
    result_left, result_right = split(concatenated)
    
    # The round-trip property is violated when left contains dots
    if "." in left_with_dots:
        # Split will only take up to the first dot!
        first_part = left_with_dots.split(".")[0]
        assert result_left == first_part
        # Everything after the first dot becomes part of right
        remaining = ".".join(left_with_dots.split(".")[1:])
        if remaining:
            assert result_right == f"{remaining}.{right}"
        else:
            assert result_right == right
        
        # Confirm the bug: round-trip is broken
        assert (result_left, result_right) != (left_with_dots, right)


# Test with common API key patterns that might break
@given(
    prefix=st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=4, max_size=8),
    secret=st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=16, max_size=32)
)
def test_normal_api_key_pattern(prefix, secret):
    """Test with normal API key patterns (no dots) - should always work"""
    from rest_framework_api_key.crypto import concatenate, split
    
    concatenated = concatenate(prefix, secret)
    result_prefix, result_secret = split(concatenated)
    
    assert result_prefix == prefix
    assert result_secret == secret


if __name__ == "__main__":
    # Run the direct bug demonstration
    test_round_trip_bug_example()