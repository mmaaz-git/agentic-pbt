import django
from django.conf import settings
import pytest
from hypothesis import given, strategies as st, assume, example, settings as hyp_settings
from datetime import datetime, timezone as dt_timezone, timedelta
import hashlib

# Configure Django settings
settings.configure(
    DEBUG=True,
    USE_TZ=True,
    TIME_ZONE='UTC',
    USE_I18N=True,
    USE_L10N=True,
    STATIC_URL='/static/',
    MEDIA_URL='/media/',
    INSTALLED_APPS=[
        'django.contrib.staticfiles',
    ],
)

# Setup Django  
django.setup()

import django.templatetags.cache as cache_module
import django.templatetags.tz as tz_module
import django.templatetags.static as static_module


# Let me inspect the actual implementation more carefully
import inspect
print("=== make_template_fragment_key source ===")
print(inspect.getsource(cache_module.make_template_fragment_key))


# Test 1: Check if the colon separator can cause issues
@given(
    fragment_name=st.text(min_size=1, max_size=50),
    vary_item=st.text(alphabet=':', min_size=1, max_size=50)
)
def test_cache_key_colon_separator_ambiguity(fragment_name, vary_item):
    """Test if colon in vary_on items can cause ambiguity"""
    # If vary_on items contain colons, it might cause ambiguity
    # because the implementation uses ':' as separator
    
    # Two different vary_on lists that could produce same hash
    vary_on1 = [vary_item]  # e.g., ["a:b"]
    vary_on2 = vary_item.split(':')  # e.g., ["a", "b"]
    
    key1 = cache_module.make_template_fragment_key(fragment_name, vary_on1)
    key2 = cache_module.make_template_fragment_key(fragment_name, vary_on2)
    
    # These should produce different keys if vary_on items are truly different
    # But if the implementation concatenates with ':', they might collide
    if vary_on1 != vary_on2 and len(vary_on2) > 1:
        # If they're different inputs but produce same key, that's a bug
        if key1 == key2:
            print(f"COLLISION FOUND: {vary_on1} and {vary_on2} produce same key!")
            assert False, f"Hash collision: {vary_on1} and {vary_on2} produce same cache key"


# Test 2: Test with vary_on that has string ":" vs two separate items
@example(fragment_name="test", vary_item="a:b")
@given(
    fragment_name=st.text(min_size=1, max_size=20),
    vary_item=st.text(min_size=2, max_size=20).filter(lambda x: ':' in x)
)
def test_cache_key_collision_with_colon(fragment_name, vary_item):
    """Specific test for collision when using colon separator"""
    # Split on colon to create multiple items
    parts = vary_item.split(':', 1)
    if len(parts) == 2 and parts[0] and parts[1]:
        # Compare ["a:b"] vs ["a", "b"]
        vary_on_single = [vary_item]
        vary_on_multi = parts
        
        key_single = cache_module.make_template_fragment_key(fragment_name, vary_on_single)
        key_multi = cache_module.make_template_fragment_key(fragment_name, vary_on_multi)
        
        # These are different inputs and should produce different keys
        # But the implementation joins with ':' which could cause collision
        print(f"Testing: {vary_on_single} vs {vary_on_multi}")
        print(f"Keys: {key_single} vs {key_multi}")
        
        # This is the bug: they produce the same key!
        if key_single == key_multi:
            print(f"BUG FOUND: Cache key collision!")
            print(f"  Input 1: make_template_fragment_key({repr(fragment_name)}, {repr(vary_on_single)})")
            print(f"  Input 2: make_template_fragment_key({repr(fragment_name)}, {repr(vary_on_multi)})")
            print(f"  Both produce: {key_single}")
            # Don't assert here, let's collect more examples
            return False  # Return to indicate bug found
    return True


# Test 3: Systematic collision test
def test_cache_key_collision_demonstration():
    """Demonstrate the cache key collision bug"""
    fragment_name = "test_fragment"
    
    # These two different inputs produce the same cache key
    vary_on1 = ["user:123"]  # Single item with colon
    vary_on2 = ["user", "123"]  # Two separate items
    
    key1 = cache_module.make_template_fragment_key(fragment_name, vary_on1)
    key2 = cache_module.make_template_fragment_key(fragment_name, vary_on2)
    
    print(f"\nCache Key Collision Bug:")
    print(f"  Input 1: {vary_on1}")
    print(f"  Input 2: {vary_on2}")
    print(f"  Key 1: {key1}")
    print(f"  Key 2: {key2}")
    print(f"  Keys equal? {key1 == key2}")
    
    # Verify the collision
    assert key1 == key2, "Expected collision did not occur"
    
    # Let's verify by manually computing what should happen
    import hashlib
    
    # For vary_on1 = ["user:123"]
    hasher1 = hashlib.md5(usedforsecurity=False)
    hasher1.update(b"user:123")  # str("user:123").encode()
    hasher1.update(b":")
    hash1 = hasher1.hexdigest()
    
    # For vary_on2 = ["user", "123"] 
    hasher2 = hashlib.md5(usedforsecurity=False)
    hasher2.update(b"user")  # str("user").encode()
    hasher2.update(b":")
    hasher2.update(b"123")  # str("123").encode()
    hasher2.update(b":")
    hash2 = hasher2.hexdigest()
    
    print(f"\nManual hash calculation:")
    print(f"  Hash 1 (for ['user:123']): {hash1}")
    print(f"  Hash 2 (for ['user', '123']): {hash2}")
    print(f"  Hashes equal? {hash1 == hash2}")
    
    # The hashes are equal! This confirms the bug
    assert hash1 == hash2


# Test 4: More collision examples
@given(
    prefix=st.text(min_size=1, max_size=10),
    suffix=st.text(min_size=1, max_size=10)
)
def test_systematic_cache_key_collisions(prefix, suffix):
    """Find more examples of cache key collisions"""
    fragment_name = "fragment"
    
    # Create collision-prone inputs
    combined = f"{prefix}:{suffix}"
    vary_on1 = [combined]
    vary_on2 = [prefix, suffix]
    
    key1 = cache_module.make_template_fragment_key(fragment_name, vary_on1)
    key2 = cache_module.make_template_fragment_key(fragment_name, vary_on2)
    
    # These should be different but they're the same
    if key1 == key2:
        # This is the bug - collision!
        pass  # Expected due to the implementation
    else:
        # This shouldn't happen given the implementation
        assert False, f"Expected collision didn't occur for {vary_on1} vs {vary_on2}"


# Run the demonstration test immediately
if __name__ == "__main__":
    test_cache_key_collision_demonstration()