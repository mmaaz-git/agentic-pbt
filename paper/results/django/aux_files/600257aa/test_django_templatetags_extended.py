import django
from django.conf import settings
import pytest
from hypothesis import given, strategies as st, assume, example
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


# First, let me understand the TEMPLATE_FRAGMENT_KEY_TEMPLATE
import hashlib

def get_cache_module_template():
    """Extract the template string from cache module"""
    import django.templatetags.cache
    # Looking at the source, it uses TEMPLATE_FRAGMENT_KEY_TEMPLATE
    # Let's check what it actually is
    return getattr(django.templatetags.cache, 'TEMPLATE_FRAGMENT_KEY_TEMPLATE', 'template.cache.%s.%s')

print(f"Template format: {get_cache_module_template()}")


# Test for cache key edge cases
@given(
    fragment_name=st.text(),
    vary_on=st.lists(st.one_of(
        st.text(),
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.booleans(),
        st.none()
    ))
)
def test_cache_key_edge_cases(fragment_name, vary_on):
    """Test edge cases in cache key generation"""
    try:
        key = cache_module.make_template_fragment_key(fragment_name, vary_on)
        assert isinstance(key, str)
        
        # The key should contain the fragment name
        if fragment_name:
            # Check if the fragment name is properly incorporated
            # The template is 'template.cache.%s.%s' where first %s is fragment_name
            assert fragment_name in key or str(fragment_name) in key
    except Exception as e:
        # Check if this is an expected error
        print(f"Error with fragment_name={repr(fragment_name)}, vary_on={repr(vary_on)}: {e}")
        raise


# Test for potential format string injection
@given(
    fragment_name=st.text(alphabet='%s%d%x%()', min_size=1, max_size=50),
    vary_on=st.lists(st.text(alphabet='%s%d%x%()', min_size=1), max_size=3)
)
def test_cache_key_format_string_injection(fragment_name, vary_on):
    """Test if format string characters can cause injection issues"""
    # Should not crash or cause format string issues
    key = cache_module.make_template_fragment_key(fragment_name, vary_on)
    assert isinstance(key, str)
    
    # Verify determinism even with format string chars
    key2 = cache_module.make_template_fragment_key(fragment_name, vary_on)
    assert key == key2


# Test vary_on with objects that have unusual __str__ methods
class WeirdStr:
    def __init__(self, value):
        self.value = value
    
    def __str__(self):
        if self.value == "raise":
            raise ValueError("Weird __str__ error")
        elif self.value == "none":
            return None  # This would be a bug if not handled
        elif self.value == "recursive":
            return str(self)  # Infinite recursion
        else:
            return str(self.value)


@given(vary_type=st.sampled_from(["raise", "none", "normal"]))
def test_cache_key_weird_str_objects(vary_type):
    """Test cache key generation with objects that have problematic __str__ methods"""
    fragment_name = "test_fragment"
    
    if vary_type == "raise":
        # Object whose __str__ raises an exception
        weird_obj = WeirdStr("raise")
        # This should handle the exception gracefully or propagate it
        with pytest.raises(ValueError):
            cache_module.make_template_fragment_key(fragment_name, [weird_obj])
    
    elif vary_type == "none":
        # Object whose __str__ returns None (which would be a TypeError)
        weird_obj = WeirdStr("none")
        # This would cause TypeError: expected str, got NoneType
        with pytest.raises(TypeError):
            cache_module.make_template_fragment_key(fragment_name, [weird_obj])
    
    else:
        # Normal case
        weird_obj = WeirdStr("normal")
        key = cache_module.make_template_fragment_key(fragment_name, [weird_obj])
        assert isinstance(key, str)


# Test timezone conversion edge cases
@given(
    year=st.integers(min_value=1, max_value=9999),
    month=st.integers(min_value=1, max_value=12),
    day=st.integers(min_value=1, max_value=28),
    microsecond=st.integers(min_value=0, max_value=999999)
)
def test_timezone_microsecond_precision(year, month, day, microsecond):
    """Test if timezone conversion preserves microsecond precision"""
    from django.utils import timezone
    
    # Create datetime with microseconds
    dt = datetime(year, month, day, 12, 0, 0, microsecond)
    aware_dt = timezone.make_aware(dt, timezone.get_default_timezone())
    
    # Convert to UTC
    utc_result = tz_module.utc(aware_dt)
    
    if isinstance(utc_result, datetime):
        # Microseconds should be preserved
        assert utc_result.microsecond == microsecond


# Test static path with special URL characters
@given(
    path=st.text(alphabet='<>[]{}|\\^`', min_size=1, max_size=50)
)
def test_static_special_url_chars(path):
    """Test static() with characters that need URL encoding"""
    try:
        result = static_module.static(path)
        # Should return a string
        assert isinstance(result, str)
        # Should not have unencoded special characters that break URLs
        dangerous_chars = ['<', '>', '[', ']', '{', '}', '|', '\\', '^', '`']
        for char in dangerous_chars:
            # These should be encoded in the result
            if char in path:
                assert char not in result or '%' in result
    except Exception as e:
        print(f"Error with path={repr(path)}: {e}")
        raise


# Test for hash collision in cache keys
@given(
    data=st.data(),
    fragment_name=st.text(min_size=1, max_size=20)
)
def test_cache_key_hash_properties(data, fragment_name):
    """Test properties of the MD5 hash used in cache keys"""
    # Generate two different vary_on lists
    vary_on1 = data.draw(st.lists(st.text(min_size=1), min_size=1, max_size=5))
    vary_on2 = data.draw(st.lists(st.text(min_size=1), min_size=1, max_size=5).filter(lambda x: x != vary_on1))
    
    key1 = cache_module.make_template_fragment_key(fragment_name, vary_on1)
    key2 = cache_module.make_template_fragment_key(fragment_name, vary_on2)
    
    # Different vary_on should produce different keys (unless hash collision)
    assert key1 != key2
    
    # Keys should have consistent format
    assert key1.startswith('template.cache.')
    assert key2.startswith('template.cache.')


# Test empty fragment name
@given(vary_on=st.lists(st.text()))
def test_cache_key_empty_fragment_name(vary_on):
    """Test cache key generation with empty fragment name"""
    # Empty fragment name should still work
    key = cache_module.make_template_fragment_key("", vary_on)
    assert isinstance(key, str)
    assert 'template.cache..' in key  # Will have empty fragment name part


# Test vary_on with byte strings (potential encoding issues)
@given(
    fragment_name=st.text(min_size=1),
    byte_values=st.lists(st.binary(min_size=1, max_size=20), min_size=1, max_size=3)
)
def test_cache_key_bytes_in_vary_on(fragment_name, byte_values):
    """Test cache key generation with bytes in vary_on"""
    # bytes objects will be converted to string via str()
    key = cache_module.make_template_fragment_key(fragment_name, byte_values)
    assert isinstance(key, str)
    
    # Should be deterministic
    key2 = cache_module.make_template_fragment_key(fragment_name, byte_values)
    assert key == key2