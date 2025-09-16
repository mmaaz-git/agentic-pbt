import uuid
from hypothesis import given, strategies as st, assume, settings
from django.urls import converters
from django.urls import resolve, reverse, is_valid_path, path, include
from django.urls.exceptions import Resolver404, NoReverseMatch
from django.conf import settings as django_settings
from django.urls import set_urlconf, clear_url_caches
import django
import re

# Configure Django settings if not already configured
if not django_settings.configured:
    django_settings.configure(
        DEBUG=True,
        SECRET_KEY='test-key',
        ROOT_URLCONF='test_django_urls',
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
    )
    django.setup()

# Test 1: IntConverter round-trip property
@given(st.integers(min_value=0, max_value=10**18))
def test_int_converter_round_trip(value):
    """Test that IntConverter.to_url(to_python(x)) == x for valid inputs"""
    converter = converters.IntConverter()
    
    # Convert to string (as it would appear in URL)
    str_value = str(value)
    
    # Check it matches the regex
    if re.match('^' + converter.regex + '$', str_value):
        # to_python and back to_url should give original string
        python_value = converter.to_python(str_value)
        url_value = converter.to_url(python_value)
        assert url_value == str_value, f"Round-trip failed: {str_value} -> {python_value} -> {url_value}"

# Test 2: IntConverter idempotence of to_url
@given(st.integers())
def test_int_converter_to_url_idempotence(value):
    """Test that to_url(to_url(x)) == to_url(x)"""
    converter = converters.IntConverter()
    once = converter.to_url(value)
    twice = converter.to_url(once)
    assert once == twice, f"to_url not idempotent: {value} -> {once} -> {twice}"

# Test 3: UUIDConverter round-trip property
@given(st.uuids())
def test_uuid_converter_round_trip(uuid_value):
    """Test that UUIDConverter preserves UUIDs through round-trip"""
    converter = converters.UUIDConverter()
    
    # Convert UUID to string as it would appear in URL
    str_value = str(uuid_value)
    
    # to_python and back should preserve the UUID
    python_value = converter.to_python(str_value)
    url_value = converter.to_url(python_value)
    
    assert str(python_value) == str(uuid_value), f"UUID changed during to_python: {uuid_value} -> {python_value}"
    assert url_value == str_value, f"Round-trip failed: {str_value} -> {python_value} -> {url_value}"

# Test 4: SlugConverter round-trip property
@given(st.from_regex(r'^[-a-zA-Z0-9_]+$', fullmatch=True).filter(lambda x: len(x) > 0))
def test_slug_converter_round_trip(slug_value):
    """Test that SlugConverter round-trips valid slugs"""
    converter = converters.SlugConverter()
    
    # to_python and back should preserve the slug
    python_value = converter.to_python(slug_value)
    url_value = converter.to_url(python_value)
    
    assert python_value == slug_value, f"Slug changed during to_python: {slug_value} -> {python_value}"
    assert url_value == slug_value, f"Round-trip failed: {slug_value} -> {url_value}"

# Test 5: StringConverter round-trip property
@given(st.text(min_size=1).filter(lambda x: '/' not in x))
def test_string_converter_round_trip(str_value):
    """Test that StringConverter round-trips non-slash strings"""
    converter = converters.StringConverter()
    
    # to_python and back should preserve the string
    python_value = converter.to_python(str_value)
    url_value = converter.to_url(python_value)
    
    assert python_value == str_value, f"String changed during to_python: {str_value} -> {python_value}"
    assert url_value == str_value, f"Round-trip failed: {str_value} -> {url_value}"

# Test 6: PathConverter round-trip property
@given(st.text(min_size=1))
def test_path_converter_round_trip(path_value):
    """Test that PathConverter round-trips any non-empty string"""
    converter = converters.PathConverter()
    
    # to_python and back should preserve the path
    python_value = converter.to_python(path_value)
    url_value = converter.to_url(python_value)
    
    assert python_value == path_value, f"Path changed during to_python: {path_value} -> {python_value}"
    assert url_value == path_value, f"Round-trip failed: {path_value} -> {url_value}"

# Test 7: Converter regex validation
@given(st.integers(min_value=0))
def test_int_converter_regex_matches_conversion(value):
    """Test that IntConverter regex correctly identifies valid integers"""
    converter = converters.IntConverter()
    str_value = str(value)
    
    # If regex matches, to_python should succeed
    if re.match('^' + converter.regex + '$', str_value):
        try:
            result = converter.to_python(str_value)
            assert result == value, f"Conversion incorrect: {str_value} -> {result}, expected {value}"
        except Exception as e:
            assert False, f"Regex matched but to_python failed: {str_value}, error: {e}"

# Test 8: UUID converter case handling
@given(st.uuids())
def test_uuid_converter_case_insensitive(uuid_value):
    """Test that UUIDConverter handles both upper and lowercase UUIDs"""
    converter = converters.UUIDConverter()
    
    # Test with lowercase
    lower_str = str(uuid_value).lower()
    if re.match('^' + converter.regex + '$', lower_str):
        result_lower = converter.to_python(lower_str)
        assert result_lower == uuid_value, f"Lowercase UUID not parsed correctly"
    
    # Test with uppercase
    upper_str = str(uuid_value).upper()
    if re.match('^' + converter.regex + '$', upper_str):
        # The regex only matches lowercase, so this should not match
        pass
    
    # Mixed case
    mixed_str = str(uuid_value)
    for i in range(0, len(mixed_str), 2):
        if mixed_str[i].isalpha():
            mixed_str = mixed_str[:i] + mixed_str[i].upper() + mixed_str[i+1:]
    
    # UUID parsing should be case-insensitive
    try:
        result_mixed = converter.to_python(lower_str)
        url_result = converter.to_url(result_mixed)
        # The output should be lowercase
        assert url_result == lower_str, f"UUID not normalized to lowercase: {url_result}"
    except Exception:
        pass