"""Property-based tests for django.core.cache."""

from hypothesis import given, strategies as st, assume, settings
import django
from django.conf import settings as django_settings
import time

# Configure Django settings with cache
if not django_settings.configured:
    django_settings.configure(
        SECRET_KEY='test-secret-key',
        CACHES={
            'default': {
                'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            }
        }
    )

from django.core.cache import cache


# Test basic cache round-trip property
@given(
    st.text(min_size=1, max_size=100),  # key
    st.one_of(
        st.none(),
        st.booleans(),
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.text(),
        st.lists(st.integers()),
        st.dictionaries(st.text(), st.integers())
    )  # value
)
@settings(max_examples=1000)
def test_cache_set_get_roundtrip(key, value):
    """Test that cache.get(key) returns what was set with cache.set(key, value)."""
    # Clear cache to avoid interference
    cache.clear()
    
    # Set the value
    cache.set(key, value)
    
    # Get it back
    result = cache.get(key)
    
    # Should get the same value back
    assert result == value, f"Cache round-trip failed: {value} != {result}"


# Test cache.add (should only set if key doesn't exist)
@given(
    st.text(min_size=1, max_size=100),
    st.integers(),
    st.integers()
)
@settings(max_examples=500)
def test_cache_add_semantics(key, value1, value2):
    """Test that cache.add only sets value if key doesn't exist."""
    cache.clear()
    
    # First add should succeed
    result1 = cache.add(key, value1)
    assert result1 is True, "First add should succeed"
    assert cache.get(key) == value1, "Should get first value"
    
    # Second add should fail (key exists)
    result2 = cache.add(key, value2)
    assert result2 is False, "Second add should fail"
    assert cache.get(key) == value1, "Should still have first value"
    
    # After delete, add should succeed again
    cache.delete(key)
    result3 = cache.add(key, value2)
    assert result3 is True, "Add after delete should succeed"
    assert cache.get(key) == value2, "Should have new value"


# Test cache.get_or_set
@given(
    st.text(min_size=1, max_size=100),
    st.integers(),
    st.integers()
)
@settings(max_examples=500)
def test_cache_get_or_set(key, default_value, set_value):
    """Test cache.get_or_set behavior."""
    cache.clear()
    
    # First call should set and return default
    result1 = cache.get_or_set(key, default_value)
    assert result1 == default_value, "Should return default on first call"
    assert cache.get(key) == default_value, "Should have set the default"
    
    # Second call should return existing value, not default
    result2 = cache.get_or_set(key, set_value)
    assert result2 == default_value, "Should return existing value, not new default"
    assert cache.get(key) == default_value, "Should still have original value"


# Test cache delete returns correct boolean
@given(
    st.text(min_size=1, max_size=100),
    st.integers()
)
@settings(max_examples=500)
def test_cache_delete_return_value(key, value):
    """Test that cache.delete returns True if key existed, False otherwise."""
    cache.clear()
    
    # Delete non-existent key should return False
    result1 = cache.delete(key)
    assert result1 is False, "Deleting non-existent key should return False"
    
    # Set a value
    cache.set(key, value)
    
    # Delete existing key should return True
    result2 = cache.delete(key)
    assert result2 is True, "Deleting existing key should return True"
    
    # Key should be gone
    assert cache.get(key) is None, "Key should be deleted"
    
    # Delete again should return False
    result3 = cache.delete(key)
    assert result3 is False, "Deleting already deleted key should return False"


# Test cache with None values
@given(st.text(min_size=1, max_size=100))
@settings(max_examples=500)
def test_cache_none_value(key):
    """Test that cache correctly handles None values."""
    cache.clear()
    
    # Set None
    cache.set(key, None)
    
    # Should get None back (not default)
    result = cache.get(key, default="NOT_NONE")
    assert result is None, "Should get None, not default"
    
    # Key should exist
    assert cache.has_key(key), "Key with None value should exist"


# Test cache timeout behavior
@given(
    st.text(min_size=1, max_size=100),
    st.integers(),
    st.floats(min_value=0.001, max_value=0.1)  # Small timeout in seconds
)
@settings(max_examples=100, deadline=1000)  # Smaller sample due to time delays
def test_cache_timeout(key, value, timeout):
    """Test that cache entries expire after timeout."""
    cache.clear()
    
    # Set with timeout
    cache.set(key, value, timeout=timeout)
    
    # Should be there immediately
    assert cache.get(key) == value, "Value should be available immediately"
    
    # Wait for timeout
    time.sleep(timeout + 0.01)  # Add small buffer
    
    # Should be gone
    assert cache.get(key) is None, f"Value should expire after {timeout}s"


# Test cache versioning
@given(
    st.text(min_size=1, max_size=100),
    st.integers(),
    st.integers(min_value=0, max_value=100),
    st.integers(min_value=0, max_value=100)
)
@settings(max_examples=500)
def test_cache_versioning(key, value, version1, version2):
    """Test that cache versioning isolates values."""
    cache.clear()
    
    # Set with version1
    cache.set(key, value, version=version1)
    
    # Get with same version should work
    assert cache.get(key, version=version1) == value
    
    # Get with different version should return None
    if version1 != version2:
        assert cache.get(key, version=version2) is None
    
    # Set different value with version2
    value2 = value + 1
    cache.set(key, value2, version=version2)
    
    # Both versions should have their own values (unless they're the same version)
    if version1 == version2:
        # Same version, so both should have the new value
        assert cache.get(key, version=version1) == value2
        assert cache.get(key, version=version2) == value2
    else:
        # Different versions should have their own values
        assert cache.get(key, version=version1) == value
        assert cache.get(key, version=version2) == value2


# Test with special characters in keys
@given(
    st.text(alphabet=st.characters(blacklist_categories=('Cc', 'Cs')), min_size=1, max_size=100),
    st.integers()
)
@settings(max_examples=500)
def test_cache_special_key_characters(key, value):
    """Test cache with special characters in keys."""
    cache.clear()
    
    # Should handle any valid string as key
    cache.set(key, value)
    result = cache.get(key)
    assert result == value, f"Failed with key containing special chars"