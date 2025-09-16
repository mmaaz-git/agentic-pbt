#!/usr/bin/env python3
"""Tests specifically designed to find actual bugs in praw.models."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/praw_env/lib/python3.13/site-packages')

from hypothesis import given, assume, strategies as st, settings, example
import pytest

from praw.models.util import BoundedSet, ExponentialCounter, permissions_string


# Test BoundedSet with max_items = 0
def test_bounded_set_zero_max_bug():
    """BoundedSet with max_items=0 has undefined behavior."""
    bounded_set = BoundedSet(0)
    
    # Add multiple items
    for i in range(10):
        bounded_set.add(i)
    
    # With max_items=0, logically nothing should be stored
    # But due to implementation, it keeps the last item
    print(f"Set with max_items=0 after adding 10 items: {list(bounded_set._set.keys())}")
    print(f"Size: {len(bounded_set._set)}")
    
    # This is a bug: max_items=0 should mean empty set always
    # But it actually keeps 1 item
    if len(bounded_set._set) > 0:
        print("BUG: BoundedSet with max_items=0 stores items!")
        return True
    return False


# Test ExponentialCounter with max_counter = 0
def test_exponential_counter_zero_max_bug():
    """ExponentialCounter with max_counter=0 might have issues."""
    counter = ExponentialCounter(0)
    
    # First call should be around 1
    first = counter.counter()
    print(f"First value with max=0: {first}")
    
    # Second call - what happens when base tries to double but max is 0?
    second = counter.counter()
    print(f"Second value with max=0: {second}")
    
    # The base should be min(base * 2, max) = min(2, 0) = 0
    # Then value = 0 + jitter
    # This gives us negative or very small values
    
    # Continue calling
    values = [counter.counter() for _ in range(10)]
    print(f"Next 10 values: {values}")
    
    # Check if we get unexpected behavior
    if any(v < -0.1 for v in values):
        print("BUG: Negative values from ExponentialCounter!")
        return True
    
    return False


# Test permissions_string with permissions not in known_permissions
@given(
    known_perms=st.sets(st.text(min_size=1, max_size=3, alphabet='abc'), min_size=1, max_size=3),
    unknown_perms=st.lists(st.text(min_size=1, max_size=3, alphabet='xyz'), min_size=1, max_size=3)
)
def test_permissions_unknown_permissions(known_perms, unknown_perms):
    """Test permissions_string with permissions not in known set."""
    # Give permissions that aren't in the known set
    result = permissions_string(known_permissions=known_perms, permissions=unknown_perms)
    
    # These unknown permissions should still be added with +
    for perm in unknown_perms:
        assert f"+{perm}" in result
    
    # All known permissions should be removed with -
    for perm in known_perms:
        assert f"-{perm}" in result


# Test BoundedSet._access creating entries
def test_bounded_set_access_creates_entry_bug():
    """Test if BoundedSet._access can incorrectly create entries."""
    bounded_set = BoundedSet(3)
    
    # Add some items
    bounded_set.add(1)
    bounded_set.add(2)
    
    print(f"Initial set: {list(bounded_set._set.keys())}")
    
    # Access an item that's not in the set via __contains__
    # The __contains__ method calls _access even for non-existent items
    result = 999 in bounded_set
    
    print(f"After checking if 999 is in set: {list(bounded_set._set.keys())}")
    
    # The set should not have changed
    if 999 in bounded_set._set:
        print("BUG: Checking membership added item to set!")
        return True
    
    return False


# Test float vs int inconsistency in ExponentialCounter 
def test_exponential_counter_type_consistency():
    """Test that ExponentialCounter returns consistent types."""
    counter = ExponentialCounter(10)
    
    types_seen = set()
    for _ in range(20):
        value = counter.counter()
        types_seen.add(type(value))
    
    print(f"Types returned by counter: {types_seen}")
    
    # Should return consistent types (all float or all int)
    # But it returns int for first value, float for rest
    if len(types_seen) > 1:
        print("ISSUE: ExponentialCounter returns mixed types (int and float)")
        # This might not be a bug per se, but could cause issues
        return True
    
    return False


# Test permission_string with None in the permissions list
def test_permissions_none_in_list():
    """Test permissions_string with None as an element in the list."""
    known = {"read", "write", "execute"}
    
    # What if someone passes [None] or ["read", None]?
    try:
        result = permissions_string(known_permissions=known, permissions=[None])
        print(f"Result with [None]: {result}")
        # If this doesn't crash, check the result
        if "None" in result or "+None" in result:
            print("BUG: None is treated as string 'None'")
            return True
    except TypeError as e:
        print(f"TypeError with None in list: {e}")
        # This is probably expected behavior
        return False
    
    return False


# Test BoundedSet with negative max_items
def test_bounded_set_negative_max():
    """Test BoundedSet with negative max_items."""
    bounded_set = BoundedSet(-5)
    
    # Add items
    for i in range(10):
        bounded_set.add(i)
    
    print(f"Set with max_items=-5: {list(bounded_set._set.keys())}")
    print(f"Size: {len(bounded_set._set)}")
    
    # With negative max_items, the comparison len(self._set) > self.max_items
    # will be True when we have any items, causing immediate eviction
    # This leads to keeping only the most recent item
    
    if len(bounded_set._set) != 1:
        print(f"UNEXPECTED: Set has {len(bounded_set._set)} items with negative max")
    
    return False


# Run all bug tests
if __name__ == "__main__":
    print("Testing for actual bugs in praw.models...")
    print("=" * 60)
    
    bugs_found = []
    
    print("\n1. Testing BoundedSet with max_items=0:")
    if test_bounded_set_zero_max_bug():
        bugs_found.append("BoundedSet with max_items=0")
    
    print("\n2. Testing ExponentialCounter with max_counter=0:")
    if test_exponential_counter_zero_max_bug():
        bugs_found.append("ExponentialCounter with max_counter=0")
    
    print("\n3. Testing BoundedSet._access:")
    if test_bounded_set_access_creates_entry_bug():
        bugs_found.append("BoundedSet._access creates entries")
    
    print("\n4. Testing ExponentialCounter type consistency:")
    if test_exponential_counter_type_consistency():
        bugs_found.append("ExponentialCounter type inconsistency")
    
    print("\n5. Testing permissions with None in list:")
    if test_permissions_none_in_list():
        bugs_found.append("permissions_string with None")
    
    print("\n6. Testing BoundedSet with negative max_items:")
    if test_bounded_set_negative_max():
        bugs_found.append("BoundedSet with negative max_items")
    
    print("\n7. Testing permissions with unknown permissions:")
    test_permissions_unknown_permissions({"a", "b"}, ["x", "y"])
    
    print("\n" + "=" * 60)
    if bugs_found:
        print(f"Potential bugs/issues found: {bugs_found}")
    else:
        print("No clear bugs found, but some edge cases have undefined behavior")