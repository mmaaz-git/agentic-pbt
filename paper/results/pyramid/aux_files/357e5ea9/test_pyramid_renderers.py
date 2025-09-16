#!/usr/bin/env python3
"""Property-based tests for pyramid.renderers module."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

import json
import re
from hypothesis import given, strategies as st, assume, settings
import pyramid.renderers as renderers


# Test 1: JSONP callback validation regex
@given(st.text())
def test_jsonp_callback_validation_consistency(callback):
    """Test that JSONP callback validation is consistent with JavaScript naming rules."""
    pattern = renderers.JSONP_VALID_CALLBACK
    result = pattern.match(callback)
    
    # If it matches, verify it's actually a valid JS identifier/expression
    if result:
        # According to the regex, valid callbacks should:
        # 1. Start with $, letter, or underscore
        # 2. Continue with $, digit, letter, underscore, dot, or brackets
        # 3. Not end with a dot
        
        # Check the properties the regex claims
        assert callback[0] in '$abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_'
        assert callback[-1] != '.'
        assert len(callback) >= 2  # Must have at least 2 chars based on pattern


# Test 2: JSON round-trip for basic types
@given(
    st.one_of(
        st.none(),
        st.booleans(),
        st.integers(min_value=-1e10, max_value=1e10),
        st.floats(allow_nan=False, allow_infinity=False),
        st.text(),
        st.lists(st.integers()),
        st.dictionaries(st.text(), st.integers())
    )
)
def test_json_renderer_round_trip(value):
    """Test that JSON renderer correctly serializes JSON-serializable objects."""
    json_renderer = renderers.JSON()
    
    # Create a mock info object (renderer factories expect this)
    class MockInfo:
        pass
    
    # Get the actual render function
    render_func = json_renderer(MockInfo())
    
    # Render without request (should still work)
    system = {'request': None}
    rendered = render_func(value, system)
    
    # Should be able to deserialize back
    deserialized = json.loads(rendered)
    
    # For basic JSON types, round-trip should preserve value
    # Note: JSON converts tuples to lists, so we need to handle that
    assert deserialized == value


# Test 3: JSON custom adapter registration
@given(st.integers())
def test_json_custom_adapter(value):
    """Test that custom adapters are properly used for serialization."""
    
    class CustomType:
        def __init__(self, val):
            self.val = val
    
    def custom_adapter(obj, request):
        return obj.val * 2  # Double the value as a test
    
    json_renderer = renderers.JSON()
    json_renderer.add_adapter(CustomType, custom_adapter)
    
    class MockInfo:
        pass
    
    render_func = json_renderer(MockInfo())
    
    # Create custom object
    custom_obj = CustomType(value)
    
    # Render it
    system = {'request': None}
    rendered = render_func(custom_obj, system)
    
    # Should use our adapter
    deserialized = json.loads(rendered)
    assert deserialized == value * 2


# Test 4: JSONP output format
# Generate valid JSONP callback names according to the regex pattern
# Note: The regex requires minimum 3 characters
valid_callback_strategy = st.text(
    alphabet='$abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_',
    min_size=1,
    max_size=1
).flatmap(
    lambda first: st.text(
        alphabet='$0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_.[]',
        min_size=2,  # Changed to 2 to ensure minimum 3 total characters
        max_size=20
    ).filter(lambda s: not s[-1] == '.')  # Last char cannot be dot
    .map(lambda rest: first + rest)
)  # Must not end with dot

@given(
    valid_callback_strategy,
    st.dictionaries(st.text(), st.integers())
)
def test_jsonp_format(callback, data):
    """Test that JSONP renderer produces correct format with callback."""
    jsonp_renderer = renderers.JSONP()
    
    class MockInfo:
        pass
    
    class MockRequest:
        def __init__(self):
            self.GET = {'callback': callback}
            self.response = MockResponse()
    
    class MockResponse:
        def __init__(self):
            self.default_content_type = 'text/html'
            self.content_type = 'text/html'
    
    render_func = jsonp_renderer(MockInfo())
    
    request = MockRequest()
    system = {'request': request}
    
    rendered = render_func(data, system)
    
    # Check format: /**/callback(json_data);
    expected_prefix = f'/**/{callback}('
    expected_suffix = ');'
    
    assert rendered.startswith(expected_prefix)
    assert rendered.endswith(expected_suffix)
    
    # Extract JSON part and verify it's valid
    json_part = rendered[len(expected_prefix):-len(expected_suffix)]
    deserialized = json.loads(json_part)
    assert deserialized == data
    
    # Check content type was set correctly
    assert request.response.content_type == 'application/javascript'


# Test 5: RendererHelper.clone() preserves properties
@given(
    st.text(),
    st.text(),
)
def test_renderer_helper_clone(name, package):
    """Test that RendererHelper.clone() creates equivalent instances."""
    # Create original helper
    original = renderers.RendererHelper(name=name, package=package, registry=None)
    
    # Clone it
    cloned = original.clone()
    
    # Properties should be preserved
    assert cloned.name == original.name
    assert cloned.package == original.package
    assert cloned.registry == original.registry
    assert cloned.type == original.type
    
    # Clone with overrides
    new_name = name + "_modified" if name else "modified"
    cloned_with_override = original.clone(name=new_name)
    assert cloned_with_override.name == new_name
    assert cloned_with_override.package == original.package


# Test 6: string_renderer_factory always returns string
@given(
    st.one_of(
        st.none(),
        st.booleans(),
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.text(),
        st.lists(st.integers()),
        st.dictionaries(st.text(), st.integers()),
        st.binary()
    )
)
def test_string_renderer_factory(value):
    """Test that string_renderer_factory always returns a string."""
    class MockInfo:
        pass
    
    class MockRequest:
        def __init__(self):
            self.response = MockResponse()
    
    class MockResponse:
        def __init__(self):
            self.default_content_type = 'text/html'
            self.content_type = 'text/html'
    
    render_func = renderers.string_renderer_factory(MockInfo())
    
    # Test without request
    result = render_func(value, {'request': None})
    assert isinstance(result, str)
    assert result == str(value)
    
    # Test with request - should set content type
    request = MockRequest()
    result = render_func(value, {'request': request})
    assert isinstance(result, str)
    assert request.response.content_type == 'text/plain'


# Test 7: JSONP callback validation edge cases
@given(st.text(min_size=1, max_size=1000))
def test_jsonp_callback_validation_properties(text):
    """Test properties of JSONP callback validation."""
    pattern = renderers.JSONP_VALID_CALLBACK
    
    # Test case insensitivity (pattern has re.I flag)
    if pattern.match(text):
        # If lowercase matches, uppercase should too
        assert pattern.match(text.upper()) is not None
        assert pattern.match(text.lower()) is not None
    
    # Test that empty string never matches
    if text == "":
        assert pattern.match(text) is None
    
    # Test ending with dot always fails
    if text.endswith('.'):
        assert pattern.match(text) is None
    
    # Test starting with digit always fails
    if text and text[0].isdigit():
        assert pattern.match(text) is None


# Test 8: JSONP without callback returns plain JSON
@given(st.dictionaries(st.text(), st.integers()))
def test_jsonp_without_callback(data):
    """Test that JSONP renderer returns plain JSON when no callback is provided."""
    jsonp_renderer = renderers.JSONP()
    
    class MockInfo:
        pass
    
    class MockRequest:
        def __init__(self):
            self.GET = {}  # No callback parameter
            self.response = MockResponse()
    
    class MockResponse:
        def __init__(self):
            self.default_content_type = 'text/html'
            self.content_type = 'text/html'
    
    render_func = jsonp_renderer(MockInfo())
    
    request = MockRequest()
    system = {'request': request}
    
    rendered = render_func(data, system)
    
    # Should be plain JSON
    deserialized = json.loads(rendered)
    assert deserialized == data
    
    # Content type should be JSON
    assert request.response.content_type == 'application/json'


# Test 9: JSON __json__ method support
@given(st.integers())
def test_json_dunder_json_method(value):
    """Test that objects with __json__ method are properly serialized."""
    
    class CustomType:
        def __init__(self, val):
            self.val = val
        
        def __json__(self, request):
            return {"custom": self.val * 3}
    
    json_renderer = renderers.JSON()
    
    class MockInfo:
        pass
    
    render_func = json_renderer(MockInfo())
    
    custom_obj = CustomType(value)
    system = {'request': None}
    rendered = render_func(custom_obj, system)
    
    deserialized = json.loads(rendered)
    assert deserialized == {"custom": value * 3}


# Test 10: JSONP callback validation overly restrictive
def test_jsonp_callback_validation_too_restrictive():
    """Test that shows JSONP callback validation is overly restrictive."""
    pattern = renderers.JSONP_VALID_CALLBACK
    
    # These are all valid JavaScript identifiers that should work as callbacks
    # but are rejected by the current regex
    common_short_callbacks = [
        'cb',  # Very common abbreviation for callback
        'fn',  # Common abbreviation for function  
        'f',   # Single letter callbacks are valid JS
        '_',   # Valid JS identifier
        '$',   # jQuery-style, valid JS identifier
        'x0',  # Two chars starting with letter
        '_a',  # Two chars starting with underscore
        '$0',  # Two chars starting with $
    ]
    
    rejections = []
    for callback in common_short_callbacks:
        if not pattern.match(callback):
            rejections.append(callback)
    
    # All these valid JS identifiers are rejected
    assert rejections == common_short_callbacks
    
    # The issue is the regex requires minimum 3 characters
    # Pattern: ^[$a-z_][$0-9a-z_\.\[\]]+[^.]$
    #          1 char + 1+ chars + 1 char = minimum 3 chars
    
    # This is overly restrictive for real-world JSONP usage


# Test 11: Multiple adapter registration
@given(st.lists(st.integers(), min_size=2, max_size=10))
def test_json_multiple_adapters(values):
    """Test that multiple adapters can be registered and work correctly."""
    
    class Type1:
        def __init__(self, val):
            self.val = val
    
    class Type2:
        def __init__(self, val):
            self.val = val
    
    def adapter1(obj, request):
        return obj.val + 1000
    
    def adapter2(obj, request):
        return obj.val + 2000
    
    json_renderer = renderers.JSON()
    json_renderer.add_adapter(Type1, adapter1)
    json_renderer.add_adapter(Type2, adapter2)
    
    class MockInfo:
        pass
    
    render_func = json_renderer(MockInfo())
    
    # Test both types
    obj1 = Type1(values[0])
    obj2 = Type2(values[1])
    
    system = {'request': None}
    
    rendered1 = render_func(obj1, system)
    rendered2 = render_func(obj2, system)
    
    assert json.loads(rendered1) == values[0] + 1000
    assert json.loads(rendered2) == values[1] + 2000


if __name__ == "__main__":
    # Run a quick test to ensure imports work
    print("Running pyramid.renderers property-based tests...")
    print("All imports successful. Run with pytest to execute tests.")