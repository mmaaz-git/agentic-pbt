#!/usr/bin/env python3
"""Deep property tests to find bugs in praw.models."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/praw_env/lib/python3.13/site-packages')

from hypothesis import given, assume, strategies as st, settings
import pytest
import math

from praw.models.util import BoundedSet, ExponentialCounter, permissions_string, stream_generator
from praw.models.base import PRAWBase


# Test BoundedSet move_to_end behavior more thoroughly
@given(
    max_size=st.integers(min_value=3, max_value=10),
    initial_items=st.lists(st.integers(min_value=0, max_value=100), min_size=5, max_size=20, unique=True)
)
def test_bounded_set_lru_eviction_order(max_size, initial_items):
    """Test that BoundedSet correctly implements LRU eviction."""
    bounded_set = BoundedSet(max_size)
    
    # Add initial items (more than max_size)
    for item in initial_items[:max_size + 2]:
        bounded_set.add(item)
    
    # The oldest items should have been evicted
    # Items that should be in set: last max_size items added
    expected_items = initial_items[2:max_size + 2]
    
    for i, item in enumerate(initial_items[:max_size + 2]):
        if i < 2:  # First 2 items should be evicted
            assert item not in bounded_set
        else:  # Later items should be present
            assert item in bounded_set
    
    # Now access the third item (index 2) - this should move it to end
    third_item = initial_items[2]
    _ = third_item in bounded_set  # Access it
    
    # Add two more new items - this should evict everything except third_item
    new_item1 = max(initial_items) + 1
    new_item2 = max(initial_items) + 2
    bounded_set.add(new_item1)
    bounded_set.add(new_item2)
    
    # Third item should still be there (it was accessed recently)
    assert third_item in bounded_set
    assert new_item1 in bounded_set
    assert new_item2 in bounded_set


# Test ExponentialCounter jitter distribution
@given(
    max_counter=st.integers(min_value=10, max_value=100),
    num_samples=st.integers(min_value=100, max_value=1000)
)
@settings(max_examples=10)
def test_exponential_counter_jitter_distribution(max_counter, num_samples):
    """Test that jitter is uniformly distributed as claimed."""
    counter = ExponentialCounter(max_counter)
    
    # Collect samples at the same base level
    samples = []
    for _ in range(num_samples):
        counter.reset()  # Reset to get samples at base=1
        samples.append(counter.counter())
    
    # All samples should be between 0.9375 and 1.0625 (1 ± 1/16)
    for sample in samples:
        assert 0.9375 <= sample <= 1.0625
    
    # Check that we get good coverage of the range (statistical test)
    # With many samples, we should see values across the range
    min_sample = min(samples)
    max_sample = max(samples)
    
    # With 100+ samples, we expect to see close to full range
    assert min_sample < 0.95  # Should see some low values
    assert max_sample > 1.05  # Should see some high values


# Test permissions_string with overlapping permissions
@given(
    base_perms=st.sets(st.text(min_size=1, max_size=5, alphabet='abcde'), min_size=3, max_size=5),
)
def test_permissions_string_idempotence(base_perms):
    """Test that permission string generation is deterministic."""
    # Same inputs should produce same output
    perms_list = list(base_perms)
    
    result1 = permissions_string(known_permissions=base_perms, permissions=perms_list)
    result2 = permissions_string(known_permissions=base_perms, permissions=perms_list)
    
    assert result1 == result2
    
    # Order in the list shouldn't matter for the final result parts
    import random
    shuffled = perms_list.copy()
    random.shuffle(shuffled)
    
    result3 = permissions_string(known_permissions=base_perms, permissions=shuffled)
    
    # Parse the results to compare parts
    parts1 = set(result1.split(','))
    parts3 = set(result3.split(','))
    
    # Should have same parts regardless of input order
    assert parts1 == parts3


# Test PRAWBase._safely_add_arguments doesn't mutate
@given(
    nested_dict=st.dictionaries(
        st.text(min_size=1, max_size=5),
        st.dictionaries(
            st.text(min_size=1, max_size=5),
            st.integers(),
            min_size=0,
            max_size=3
        ),
        min_size=1,
        max_size=3
    )
)
def test_prawbase_deep_copy_safety(nested_dict):
    """Test that _safely_add_arguments truly does deep copy."""
    import copy
    
    # Create a mutable object inside the dict
    test_key = list(nested_dict.keys())[0]
    original_value = nested_dict[test_key]
    original_copy = copy.deepcopy(original_value)
    
    # Create arguments dict
    arguments = nested_dict.copy()
    
    # Call _safely_add_arguments
    PRAWBase._safely_add_arguments(
        arguments=arguments,
        key=test_key,
        new_key="test_value"
    )
    
    # Original nested dict should be unchanged
    assert original_value == original_copy
    
    # The new arguments should have the addition
    assert "new_key" in arguments[test_key]
    assert arguments[test_key]["new_key"] == "test_value"


# Test BoundedSet with hash collisions
@given(max_size=st.integers(min_value=2, max_value=10))
def test_bounded_set_hash_collision_handling(max_size):
    """Test BoundedSet with objects that might have hash collisions."""
    
    class HashCollider:
        def __init__(self, value):
            self.value = value
        
        def __hash__(self):
            # Force hash collisions
            return self.value % 2
        
        def __eq__(self, other):
            return isinstance(other, HashCollider) and self.value == other.value
    
    bounded_set = BoundedSet(max_size)
    
    # Add items that will have hash collisions
    items = [HashCollider(i) for i in range(max_size * 2)]
    
    for item in items:
        bounded_set.add(item)
        assert len(bounded_set._set) <= max_size
    
    # Check that the right items are kept (last max_size items)
    for i, item in enumerate(items):
        if i < max_size:
            assert item not in bounded_set
        else:
            assert item in bounded_set


# Test ExponentialCounter concurrent-like usage
def test_exponential_counter_state_isolation():
    """Test that multiple ExponentialCounter instances are independent."""
    counter1 = ExponentialCounter(100)
    counter2 = ExponentialCounter(100)
    
    # Advance counter1
    for _ in range(5):
        counter1.counter()
    
    # counter2 should still be at base
    value2 = counter2.counter()
    assert 0.9375 <= value2 <= 1.0625
    
    # counter1 should be higher
    value1 = counter1.counter()
    assert value1 > 10  # Should be around 32-64 range


# Test empty string handling in permissions
def test_permissions_empty_string_in_known():
    """Test permissions_string with empty string in known permissions."""
    known = {"", "read", "write"}
    given = ["read"]
    
    result = permissions_string(known_permissions=known, permissions=given)
    
    # Should handle empty string correctly
    assert "-all" in result
    assert "+read" in result
    assert "-write" in result
    assert "-" in result or "+-" in result  # Empty string handling


# Test permissions with special permission names
@given(
    special_names=st.sets(
        st.sampled_from(["all", "none", "ALL", "None", "+all", "-all", "*", "??", ""]),
        min_size=1,
        max_size=5
    )
)
def test_permissions_special_names(special_names):
    """Test permissions_string with special permission names."""
    # These special names might confuse the logic
    result = permissions_string(known_permissions=special_names, permissions=list(special_names))
    
    # Should still produce valid output
    assert result.startswith("-all")
    
    # Each permission should appear exactly once with + prefix
    for perm in special_names:
        if perm:  # Skip empty string
            # Count occurrences - should be exactly 1 with + prefix
            assert result.count(f"+{perm}") == 1


if __name__ == "__main__":
    print("Running deep property tests for praw.models...")
    
    import pytest
    pytest.main([__file__, "-v", "--tb=short", "-x"])