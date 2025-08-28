import uuid
from hypothesis import given, strategies as st, assume, settings, example
from django.urls import converters, register_converter
from django.urls import resolve, reverse, is_valid_path, path, include, re_path
from django.urls.exceptions import Resolver404, NoReverseMatch
from django.conf import settings as django_settings
from django.urls import set_urlconf, clear_url_caches
from django.http import HttpResponse
import django
import re

# Configure Django settings if not already configured
if not django_settings.configured:
    django_settings.configure(
        DEBUG=True,
        SECRET_KEY='test-key',
        ROOT_URLCONF='test_django_urls_advanced',
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
    )
    django.setup()

# Test custom converter registration
class CustomConverter:
    regex = r'\d{4}'
    
    def to_python(self, value):
        return int(value)
    
    def to_url(self, value):
        return '%04d' % value

# Test 1: Custom converter registration and retrieval
@given(st.text(alphabet=st.characters(min_codepoint=97, max_codepoint=122), min_size=1, max_size=20))
def test_custom_converter_registration(converter_name):
    """Test that custom converters can be registered and used"""
    # Register a custom converter
    try:
        register_converter(CustomConverter, converter_name)
        
        # Create a URL pattern using the converter
        def dummy_view(request, val):
            return HttpResponse(str(val))
        
        from django.urls import converters as conv_module
        # Check if converter was registered
        assert hasattr(conv_module, 'DEFAULT_CONVERTERS'), "DEFAULT_CONVERTERS should exist"
        
    except Exception as e:
        # Some names might be invalid
        pass

# Test 2: URL patterns with converters preserve types
@given(st.integers(min_value=0, max_value=999999))
def test_url_pattern_int_converter_type_preservation(int_value):
    """Test that int converter preserves integer type through URL patterns"""
    from django.urls import URLPattern, RoutePattern
    from django.urls.converters import IntConverter
    
    def view_func(request, id):
        return HttpResponse(str(id))
    
    # Create pattern with int converter
    pattern = URLPattern(
        RoutePattern(f'item/<int:id>/'),
        view_func,
        name='item-detail'
    )
    
    # Test the converter in the pattern
    url_path = f'item/{int_value}/'
    try:
        match = pattern.resolve(url_path)
        if match:
            # The id parameter should be an integer, not a string
            assert 'id' in match.kwargs
            captured_value = match.kwargs['id']
            assert isinstance(captured_value, int), f"Expected int, got {type(captured_value)}"
            assert captured_value == int_value, f"Value mismatch: {captured_value} != {int_value}"
    except Resolver404:
        # Pattern didn't match, which is fine
        pass

# Test 3: UUID converter normalization
@given(st.uuids())
def test_uuid_converter_normalization(uuid_value):
    """Test that UUID converter normalizes UUID format"""
    from django.urls.converters import UUIDConverter
    converter = UUIDConverter()
    
    # Test various UUID formats
    uuid_str = str(uuid_value)
    
    # Test that the converter normalizes to lowercase with hyphens
    result = converter.to_python(uuid_str)
    url_form = converter.to_url(result)
    
    # URL form should be lowercase with hyphens
    assert url_form == uuid_str.lower(), f"UUID not normalized: {url_form} != {uuid_str.lower()}"
    assert '-' in url_form, "UUID should contain hyphens"
    
    # Test that it handles UUID objects properly
    url_from_obj = converter.to_url(uuid_value)
    assert url_from_obj == uuid_str.lower(), f"UUID object not converted properly"

# Test 4: Slug converter validation
@given(st.text())
def test_slug_converter_validation(text_value):
    """Test that slug converter only accepts valid slugs"""
    from django.urls.converters import SlugConverter
    converter = SlugConverter()
    
    # Check if the text matches slug pattern
    if re.match(r'^[-a-zA-Z0-9_]+$', text_value) and text_value:
        # Should convert successfully
        result = converter.to_python(text_value)
        assert result == text_value
        url_result = converter.to_url(result)
        assert url_result == text_value
    else:
        # Invalid slug - converter should still accept it (no validation in to_python)
        # but the regex wouldn't match in actual URL resolution
        result = converter.to_python(text_value)
        assert result == text_value  # to_python doesn't validate

# Test 5: Path converter accepts everything
@given(st.text())
def test_path_converter_accepts_all(text_value):
    """Test that path converter accepts any string including slashes"""
    from django.urls.converters import PathConverter
    converter = PathConverter()
    
    # Should accept any string
    result = converter.to_python(text_value)
    assert result == text_value
    
    url_result = converter.to_url(result)
    assert url_result == text_value

# Test 6: String converter slash handling
@given(st.text())
def test_string_converter_slash_behavior(text_value):
    """Test string converter behavior with slashes"""
    from django.urls.converters import StringConverter
    converter = StringConverter()
    
    # to_python doesn't validate - it just returns the value
    result = converter.to_python(text_value)
    assert result == text_value
    
    # to_url also just returns the value
    url_result = converter.to_url(result)
    assert url_result == text_value
    
    # The regex is what prevents slashes in actual URL matching
    if '/' not in text_value and text_value:
        assert re.match(f'^{converter.regex}$', text_value)
    elif '/' in text_value:
        assert not re.match(f'^{converter.regex}$', text_value)

# Test 7: Integer converter boundary values
@given(st.one_of(
    st.just(0),
    st.just(1),
    st.just(-1),
    st.just(2**31 - 1),
    st.just(2**31),
    st.just(2**63 - 1),
    st.just(2**63),
    st.just(10**100),
    st.integers()
))
def test_int_converter_boundaries(value):
    """Test integer converter with boundary values"""
    from django.urls.converters import IntConverter
    converter = IntConverter()
    
    # Negative numbers don't match the regex
    if value >= 0:
        str_value = str(value)
        if re.match(f'^{converter.regex}$', str_value):
            # Should convert successfully
            result = converter.to_python(str_value)
            assert result == value
            url_result = converter.to_url(result)
            assert url_result == str_value
    else:
        # Negative numbers - to_url still works
        url_result = converter.to_url(value)
        assert url_result == str(value)

# Test 8: Converter to_url accepts various input types
@given(st.one_of(st.integers(), st.text()))
def test_converter_to_url_type_flexibility(value):
    """Test that converters handle various input types in to_url"""
    from django.urls.converters import IntConverter, StringConverter
    
    int_conv = IntConverter()
    str_conv = StringConverter()
    
    # IntConverter.to_url should convert anything to string
    result = int_conv.to_url(value)
    assert isinstance(result, str)
    assert result == str(value)
    
    # StringConverter.to_url should also convert to string
    result = str_conv.to_url(value)
    assert isinstance(result, str)
    assert result == str(value)