import django
from django.conf import settings
import pytest
from hypothesis import given, strategies as st, assume, settings as hyp_settings
from datetime import datetime, timezone as dt_timezone
import zoneinfo
import hashlib

# Configure Django settings
settings.configure(
    DEBUG=True,
    USE_TZ=True,
    TIME_ZONE='UTC',
    USE_I18N=True,
    USE_L10N=True,
    STATIC_URL='/static/',
    INSTALLED_APPS=[
        'django.contrib.staticfiles',
    ],
)

# Setup Django
django.setup()

import django.templatetags.cache as cache_module
import django.templatetags.tz as tz_module
import django.templatetags.static as static_module


# Test 1: cache.make_template_fragment_key determinism
@given(
    fragment_name=st.text(min_size=1, max_size=100),
    vary_on1=st.lists(st.one_of(st.text(), st.integers(), st.floats(allow_nan=False))),
    vary_on2=st.lists(st.one_of(st.text(), st.integers(), st.floats(allow_nan=False))),
)
def test_cache_key_deterministic(fragment_name, vary_on1, vary_on2):
    """Same inputs should produce same cache key output"""
    # Test determinism - same inputs produce same output
    key1a = cache_module.make_template_fragment_key(fragment_name, vary_on1)
    key1b = cache_module.make_template_fragment_key(fragment_name, vary_on1)
    assert key1a == key1b
    
    # Different vary_on should produce different keys
    if vary_on1 != vary_on2:
        key2 = cache_module.make_template_fragment_key(fragment_name, vary_on2)
        assert key1a != key2


# Test 2: cache key with None vs empty list
@given(fragment_name=st.text(min_size=1, max_size=100))
def test_cache_key_none_vs_empty(fragment_name):
    """Test if None and empty list produce different keys as they represent different cases"""
    key_none = cache_module.make_template_fragment_key(fragment_name, None)
    key_empty = cache_module.make_template_fragment_key(fragment_name, [])
    # These should be the same since empty list produces no hash content
    assert key_none == key_empty


# Test 3: Order matters in vary_on
@given(
    fragment_name=st.text(min_size=1, max_size=100),
    items=st.lists(st.text(min_size=1), min_size=2, max_size=5, unique=True)
)
def test_cache_key_order_matters(fragment_name, items):
    """Order of vary_on items should matter for cache keys"""
    key1 = cache_module.make_template_fragment_key(fragment_name, items)
    reversed_items = list(reversed(items))
    key2 = cache_module.make_template_fragment_key(fragment_name, reversed_items)
    # Different order should produce different keys
    assert key1 != key2


# Test 4: Static URL joining property
@given(path=st.text().filter(lambda x: not x.startswith('http')))
def test_static_url_property(path):
    """static() should produce valid URL paths"""
    result = static_module.static(path)
    # Result should be a string
    assert isinstance(result, str)
    # Result should contain the path
    if path:
        # URL-encoded version might differ but path should be in there somehow
        assert path in result or path.replace('/', '%2F') in result or path.replace(' ', '%20') in result


# Test 5: Timezone conversion properties
@given(
    year=st.integers(min_value=1900, max_value=2100),
    month=st.integers(min_value=1, max_value=12),
    day=st.integers(min_value=1, max_value=28),  # Avoid day overflow issues
    hour=st.integers(min_value=0, max_value=23),
    minute=st.integers(min_value=0, max_value=59),
    second=st.integers(min_value=0, max_value=59),
)
def test_timezone_utc_conversion(year, month, day, hour, minute, second):
    """Converting to UTC should preserve the moment in time"""
    # Create a naive datetime
    naive_dt = datetime(year, month, day, hour, minute, second)
    
    # Convert to UTC using the filter
    utc_result = tz_module.utc(naive_dt)
    
    # The function returns empty string for naive datetimes, so test with aware datetime
    from django.utils import timezone
    aware_dt = timezone.make_aware(naive_dt, timezone.get_default_timezone())
    utc_result = tz_module.utc(aware_dt)
    
    # Result should be a datetime or empty string
    assert isinstance(utc_result, (datetime, str))
    
    if isinstance(utc_result, datetime):
        # The UTC time should have UTC timezone
        assert utc_result.tzinfo is not None


# Test 6: do_timezone with invalid inputs
@given(
    invalid_value=st.one_of(st.text(), st.integers(), st.floats(), st.lists(st.integers())),
    tz_arg=st.text()
)
def test_do_timezone_invalid_inputs(invalid_value, tz_arg):
    """do_timezone should return empty string for non-datetime inputs"""
    result = tz_module.do_timezone(invalid_value, tz_arg)
    # Should return empty string for non-datetime values
    assert result == ""


# Test 7: Fragment key collision resistance
@given(
    names=st.lists(st.text(min_size=1, max_size=20), min_size=2, max_size=10, unique=True),
    vary_on=st.lists(st.text(min_size=1), max_size=5)
)
def test_cache_key_no_collisions(names, vary_on):
    """Different fragment names should produce different keys"""
    keys = [cache_module.make_template_fragment_key(name, vary_on) for name in names]
    # All keys should be unique for different fragment names
    assert len(keys) == len(set(keys))


# Test 8: Special characters in cache keys
@given(
    fragment_name=st.text(alphabet='<>:"/\\|?*\n\r\t', min_size=1, max_size=50),
    vary_on=st.lists(st.text(alphabet='<>:"/\\|?*\n\r\t', min_size=1), max_size=3)
)
def test_cache_key_special_chars(fragment_name, vary_on):
    """Cache keys should handle special characters without crashing"""
    # Should not crash with special characters
    key = cache_module.make_template_fragment_key(fragment_name, vary_on)
    assert isinstance(key, str)
    assert len(key) > 0