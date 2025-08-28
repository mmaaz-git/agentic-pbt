#!/usr/bin/env python3
"""
Comprehensive property-based tests for sentinels module.
These tests explore edge cases and potential bugs.
"""
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/sentinels_env/lib/python3.13/site-packages')

import pickle
from hypothesis import given, strategies as st, settings, assume
from sentinels import Sentinel


# Strategy for valid sentinel names - testing edge cases
sentinel_names = st.one_of(
    st.text(min_size=1),  # Normal text
    st.text(min_size=0, max_size=0),  # Empty string
    st.text(alphabet="<>", min_size=1, max_size=10),  # HTML-like chars
    st.text(alphabet="\n\r\t\0", min_size=1, max_size=3),  # Control chars
    st.text(alphabet="🦄🎉🌈", min_size=1, max_size=5),  # Unicode
)


@given(sentinel_names)
def test_singleton_invariant_comprehensive(name):
    """Test singleton property with edge case names."""
    s1 = Sentinel(name)
    s2 = Sentinel(name)
    assert s1 is s2, f"Singleton violated for name: {repr(name)}"


@given(sentinel_names)  
def test_repr_injection_vulnerability(name):
    """Test if repr format can be exploited with special characters."""
    s = Sentinel(name)
    repr_str = repr(s)
    
    # Check basic format
    assert repr_str.startswith("<"), f"Repr doesn't start with '<' for {repr(name)}"
    assert repr_str.endswith(">"), f"Repr doesn't end with '>' for {repr(name)}"
    
    # The actual name should be between the brackets
    inner = repr_str[1:-1]
    assert inner == name, f"Repr inner mismatch: expected {repr(name)}, got {repr(inner)}"


@given(st.lists(sentinel_names, min_size=2, max_size=10, unique=True))
def test_registry_pollution(names):
    """Test if creating many sentinels causes registry issues."""
    sentinels = []
    for name in names:
        s = Sentinel(name)
        sentinels.append(s)
        
        # Verify it's in registry
        assert name in Sentinel._existing_instances
        assert Sentinel._existing_instances[name] is s
    
    # Verify all are still accessible
    for name, original in zip(names, sentinels):
        retrieved = Sentinel(name)
        assert retrieved is original


@given(sentinel_names)
def test_pickle_with_empty_registry(name):
    """Test pickle behavior when registry is manipulated."""
    # Create sentinel
    s1 = Sentinel(name)
    s1_id = id(s1)
    
    # Pickle it
    pickled = pickle.dumps(s1)
    
    # Clear registry (simulating potential issue)
    Sentinel._existing_instances.clear()
    
    # Create new sentinel with same name
    s2 = Sentinel(name)
    s2_id = id(s2)
    
    # Now unpickle - what happens?
    unpickled = pickle.loads(pickled)
    
    # The unpickled should match what's in the registry (s2), not the original
    assert unpickled is s2, f"Unpickled sentinel doesn't match registry entry"
    assert unpickled is not s1, f"Unpickled matched cleared object (memory issue?)"


@given(sentinel_names)
def test_concurrent_creation_simulation(name):
    """Simulate concurrent creation (not truly concurrent, but tests edge cases)."""
    # Store original __new__ to restore later
    original_new = Sentinel.__new__
    call_count = [0]
    
    def counting_new(cls, name, obj_id=None):
        call_count[0] += 1
        return original_new(cls, name, obj_id)
    
    # Temporarily replace __new__
    Sentinel.__new__ = counting_new
    
    try:
        s1 = Sentinel(name)
        s2 = Sentinel(name)
        
        # Should only create once due to singleton
        assert call_count[0] == 1, f"__new__ called {call_count[0]} times for same name"
        assert s1 is s2
    finally:
        Sentinel.__new__ = original_new


@given(st.text(min_size=0, max_size=1000))
def test_name_attribute_immutability(name):
    """Test that sentinel's name cannot be changed after creation."""
    s = Sentinel(name)
    
    # Try to change the name
    try:
        s._name = "different"
        # If we get here, check if it actually changed
        assert s._name == "different", "Name change attempted but didn't take effect"
        
        # Check if this breaks the singleton property
        s2 = Sentinel(name)
        if s2 is s:
            # Bug: Changed name but still returns same object for old name
            print(f"BUG: Sentinel name changed but registry not updated for {repr(name)}")
    except AttributeError:
        # Good - name is protected
        pass


@given(st.lists(sentinel_names, min_size=1, max_size=100))
def test_registry_memory_leak(names):
    """Test if creating many sentinels causes memory issues."""
    initial_count = len(Sentinel._existing_instances)
    
    for name in names:
        Sentinel(name)
    
    final_count = len(Sentinel._existing_instances)
    unique_names = len(set(names))
    
    # Registry should only grow by number of unique names
    assert final_count - initial_count == unique_names, \
        f"Registry grew by {final_count - initial_count} but only {unique_names} unique names"


@given(sentinel_names)
def test_hash_consistency(name):
    """Test if sentinels can be used as dict keys reliably."""
    s1 = Sentinel(name)
    s2 = Sentinel(name)
    
    d = {s1: "value"}
    
    # Should be able to access with s2 since they're the same object
    assert s2 in d
    assert d[s2] == "value"
    
    # Hash should be consistent
    assert hash(s1) == hash(s2)


if __name__ == "__main__":
    # Run a few critical tests manually
    print("Testing edge cases...")
    
    # Test 1: Empty string
    try:
        test_singleton_invariant_comprehensive("")
        print("✓ Empty string singleton works")
    except Exception as e:
        print(f"✗ Empty string failed: {e}")
    
    # Test 2: Special characters in repr
    try:
        test_repr_injection_vulnerability("><")
        print("✓ Special characters in repr handled")
    except Exception as e:
        print(f"✗ Special characters failed: {e}")
    
    # Test 3: Registry manipulation
    try:
        test_pickle_with_empty_registry("test")
        print("✓ Pickle with registry manipulation handled")
    except Exception as e:
        print(f"✗ Registry manipulation issue: {e}")
    
    print("\nRun with pytest for full property-based testing.")