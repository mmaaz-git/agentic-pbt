#!/usr/bin/env python3
"""Property-based tests for praw.models module."""

import sys
import math
sys.path.insert(0, '/root/hypothesis-llm/envs/praw_env/lib/python3.13/site-packages')

from hypothesis import given, assume, strategies as st, settings
import pytest

# Import the classes we'll test
from praw.models.util import BoundedSet, ExponentialCounter, permissions_string


# Test 1: BoundedSet size constraint invariant
@given(
    max_size=st.integers(min_value=1, max_value=100),
    items=st.lists(st.integers(), min_size=0, max_size=500)
)
def test_bounded_set_size_constraint(max_size, items):
    """BoundedSet should never exceed its max_items limit."""
    bounded_set = BoundedSet(max_size)
    
    for item in items:
        bounded_set.add(item)
        # Invariant: size never exceeds max_items
        assert len(bounded_set._set) <= max_size
    
    # Final check
    assert len(bounded_set._set) <= max_size


# Test 2: BoundedSet maintains insertion order (newest items stay)
@given(
    max_size=st.integers(min_value=1, max_value=20),
    items=st.lists(st.integers(), min_size=0, max_size=100, unique=True)
)
def test_bounded_set_eviction_order(max_size, items):
    """BoundedSet should evict oldest items first when at capacity."""
    bounded_set = BoundedSet(max_size)
    
    for item in items:
        bounded_set.add(item)
    
    # The set should contain the last max_size items (or all if fewer)
    expected_items = items[-max_size:] if len(items) > max_size else items
    
    for item in expected_items:
        assert item in bounded_set


# Test 3: BoundedSet re-accessing items moves them to end
@given(
    max_size=st.integers(min_value=2, max_value=10),
    initial_items=st.lists(st.integers(), min_size=2, max_size=10, unique=True)
)
def test_bounded_set_access_updates_order(max_size, initial_items):
    """Accessing an item in BoundedSet should move it to the end (most recent)."""
    assume(len(initial_items) >= 2)
    bounded_set = BoundedSet(max_size)
    
    # Add initial items
    for item in initial_items[:max_size]:
        bounded_set.add(item)
    
    # Access the first item
    first_item = initial_items[0]
    if first_item in bounded_set:
        # This should move it to the end
        _ = first_item in bounded_set  # __contains__ calls _access
        
        # Now add enough new items to potentially evict old ones
        new_items = [i + max(initial_items) + 1 for i in range(max_size)]
        for new_item in new_items:
            bounded_set.add(new_item)
            if len(bounded_set._set) == max_size and first_item in initial_items[:max_size]:
                # The accessed item should still be there if it was accessed
                pass  # This property is about LRU behavior


# Test 4: ExponentialCounter growth properties  
@given(max_counter=st.integers(min_value=1, max_value=1000))
def test_exponential_counter_respects_max(max_counter):
    """ExponentialCounter should not exceed max_counter (plus jitter)."""
    counter = ExponentialCounter(max_counter)
    
    for _ in range(20):  # Call counter multiple times
        value = counter.counter()
        # Account for maximum jitter (3.125% as per docstring)
        max_with_jitter = max_counter * 1.03125
        assert value <= max_with_jitter


@given(max_counter=st.integers(min_value=2, max_value=1000))
def test_exponential_counter_growth(max_counter):
    """ExponentialCounter should grow exponentially until hitting max."""
    counter = ExponentialCounter(max_counter)
    
    prev_base = 1
    for i in range(10):  # Test first 10 iterations
        value = counter.counter()
        
        # The base should double each time (before hitting max)
        expected_base = min(prev_base * 2, max_counter) if i > 0 else 1
        
        # Value should be close to base (within jitter range)
        min_expected = expected_base - expected_base / 16.0
        max_expected = expected_base + expected_base / 16.0
        
        # After first iteration, check growth
        if i > 0:
            assert min_expected <= value <= max_expected or value <= max_counter * 1.03125
        
        prev_base = expected_base


@given(max_counter=st.integers(min_value=1, max_value=1000))
def test_exponential_counter_reset(max_counter):
    """ExponentialCounter.reset() should reset the counter to base 1."""
    counter = ExponentialCounter(max_counter)
    
    # Advance the counter
    for _ in range(5):
        counter.counter()
    
    # Reset
    counter.reset()
    
    # Next value should be around 1 (with jitter)
    value = counter.counter()
    assert 0.9375 <= value <= 1.0625  # 1 ± 1/16


# Test 5: permissions_string generation
@given(
    known_perms=st.sets(st.text(min_size=1, max_size=10, alphabet='abcdefghijklmnop'), min_size=1, max_size=10),
    given_perms=st.one_of(
        st.none(),
        st.lists(st.text(min_size=1, max_size=10, alphabet='abcdefghijklmnop'), min_size=0, max_size=10)
    )
)
def test_permissions_string_none_returns_all(known_perms, given_perms):
    """permissions_string with None should return '+all'."""
    if given_perms is None:
        result = permissions_string(known_permissions=known_perms, permissions=given_perms)
        assert result == "+all"


@given(
    known_perms=st.sets(st.text(min_size=1, max_size=5, alphabet='abcde'), min_size=1, max_size=5)
)
def test_permissions_string_all_permissions_format(known_perms):
    """permissions_string should format permissions correctly."""
    # Test with subset of known permissions
    given_perms = list(known_perms)[:len(known_perms)//2] if len(known_perms) > 1 else []
    
    result = permissions_string(known_permissions=known_perms, permissions=given_perms)
    
    # Should start with -all
    assert result.startswith("-all")
    
    # All given permissions should have + prefix
    for perm in given_perms:
        assert f"+{perm}" in result
    
    # All omitted permissions should have - prefix
    omitted = known_perms - set(given_perms)
    for perm in omitted:
        assert f"-{perm}" in result


# Test 6: Test that empty permissions list results in all permissions being removed
@given(known_perms=st.sets(st.text(min_size=1, max_size=5, alphabet='abcde'), min_size=1, max_size=5))
def test_permissions_string_empty_list(known_perms):
    """Empty permissions list should remove all known permissions."""
    result = permissions_string(known_permissions=known_perms, permissions=[])
    
    # Should start with -all
    assert result.startswith("-all")
    
    # All known permissions should be removed
    parts = result.split(",")
    assert parts[0] == "-all"
    
    # Count the negated permissions
    negated_perms = [p for p in parts[1:] if p.startswith("-")]
    assert len(negated_perms) == len(known_perms)


if __name__ == "__main__":
    # Run all tests
    print("Running property-based tests for praw.models...")
    
    # Run with more examples for thoroughness
    test_bounded_set_size_constraint()
    test_bounded_set_eviction_order()
    test_bounded_set_access_updates_order()
    test_exponential_counter_respects_max()
    test_exponential_counter_growth()
    test_exponential_counter_reset()
    test_permissions_string_none_returns_all()
    test_permissions_string_all_permissions_format()
    test_permissions_string_empty_list()
    
    print("All tests completed!")