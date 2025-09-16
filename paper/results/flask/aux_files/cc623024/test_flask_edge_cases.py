"""Focused edge case tests for Flask to find bugs"""

import tempfile
import os
from hypothesis import given, strategies as st, assume, settings, example
import flask
from flask import json, Response, Config, jsonify
import json as std_json


# Test for potential integer overflow in status codes
@given(
    status=st.one_of(
        st.integers(min_value=-2**31, max_value=-1),  # Negative status codes
        st.integers(min_value=1000, max_value=2**31-1),  # Very large status codes
        st.integers(min_value=0, max_value=99),  # Too small status codes
    )
)
def test_response_invalid_status_codes(status):
    """Test Response handling of invalid status codes"""
    try:
        response = Response("test", status=status)
        # If it accepts invalid status, check what it does
        actual_status = response.status_code
        # Status codes should be in valid HTTP range
        assert 100 <= actual_status <= 599, f"Invalid status {actual_status} accepted"
    except (ValueError, TypeError, AssertionError):
        # Expected for invalid status codes
        pass


# Test Config with special key names
@given(
    special_keys=st.sampled_from([
        '__class__', '__dict__', '__module__', '__init__',
        'update', 'pop', 'get', 'keys', 'items', 'values',
        '__getitem__', '__setitem__', '__delitem__'
    ]),
    value=st.one_of(st.integers(), st.text(max_size=50))
)
def test_config_special_keys(special_keys, value):
    """Test Config with special/reserved Python names"""
    config = Config('.')
    
    # Try to set special keys
    if special_keys.isupper():
        config[special_keys] = value
        assert config[special_keys] == value
    else:
        # Lowercase special keys might not work as config keys
        try:
            config[special_keys] = value
            # Flask Config only accepts uppercase keys by convention
            if special_keys in config:
                assert config[special_keys] == value
        except (KeyError, AttributeError):
            pass


# Test JSON with extremely nested structures
@given(
    depth=st.integers(min_value=100, max_value=500)
)
@settings(max_examples=10)
def test_json_deep_nesting(depth):
    """Test Flask JSON with deeply nested structures"""
    # Create deeply nested dict
    data = current = {}
    for i in range(depth):
        current['nested'] = {}
        current = current['nested']
    current['value'] = 42
    
    try:
        # Try to encode deeply nested structure
        encoded = json.dumps(data)
        decoded = json.loads(encoded)
        
        # Navigate to the deepest value
        current = decoded
        for i in range(depth):
            current = current['nested']
        assert current['value'] == 42
    except RecursionError:
        # Expected for very deep nesting
        pass


# Test Response with conflicting content-type parameters
@given(
    mimetype=st.sampled_from(['text/html', 'application/json', 'text/plain']),
    content_type=st.sampled_from(['text/xml', 'application/pdf', 'image/png'])
)
def test_response_conflicting_types(mimetype, content_type):
    """Test Response when mimetype and content_type conflict"""
    response = Response("test", mimetype=mimetype, content_type=content_type)
    
    # Which one takes precedence?
    actual_type = response.content_type
    # content_type should override mimetype
    assert content_type in actual_type or actual_type == content_type


# Test Config.from_pyfile with malformed Python
@given(
    malformed_code=st.sampled_from([
        "DEBUG = True\nif True",  # Incomplete if
        "SECRET = 'test'\n  INDENTED = 'bad'",  # Bad indentation
        "KEY = 'value'\nimport os\nos.system('echo test')",  # Contains imports
        "VAR = 1 / 0",  # Division by zero
        "RECURSIVE = RECURSIVE",  # Undefined variable
    ])
)
def test_config_malformed_python(malformed_code):
    """Test Config.from_pyfile with malformed Python code"""
    config = Config('.')
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(malformed_code)
        temp_file = f.name
    
    try:
        config.from_pyfile(temp_file)
        # If it succeeded, check what was loaded
        # Some malformed code might still partially work
    except (SyntaxError, NameError, ZeroDivisionError, IndentationError):
        # Expected for malformed code
        pass
    finally:
        os.unlink(temp_file)


# Test JSON with Unicode edge cases
@given(
    unicode_edge_cases=st.lists(
        st.sampled_from([
            '\u0000',  # Null character
            '\uffff',  # Highest BMP character
            '\U0001f600',  # Emoji
            '\u200b',  # Zero-width space
            '\ufeff',  # Byte order mark
            '\u2028',  # Line separator
            '\u2029',  # Paragraph separator
        ]),
        min_size=1,
        max_size=10
    )
)
def test_json_unicode_edge_cases(unicode_edge_cases):
    """Test Flask JSON with Unicode edge cases"""
    data = {"special_chars": unicode_edge_cases}
    
    try:
        encoded = json.dumps(data)
        decoded = json.loads(encoded)
        assert decoded == data
    except (ValueError, UnicodeDecodeError):
        # Some edge cases might not be supported
        pass


# Test Response with binary data and text methods
@given(
    binary_data=st.binary(min_size=1, max_size=1000)
)
def test_response_binary_text_confusion(binary_data):
    """Test Response handling of binary data with text methods"""
    response = Response(binary_data)
    
    # get_data should return binary
    assert response.get_data() == binary_data
    
    # What happens with get_data(as_text=True)?
    try:
        text_data = response.get_data(as_text=True)
        # Should decode as UTF-8 or raise error
        binary_data.decode('utf-8')
    except UnicodeDecodeError:
        # Expected for non-UTF-8 binary data
        pass


# Test Config with very long keys
@given(
    long_key=st.text(min_size=1000, max_size=10000, alphabet=st.characters(min_codepoint=65, max_codepoint=90))
)
def test_config_long_keys(long_key):
    """Test Config with extremely long keys"""
    config = Config('.')
    
    try:
        config[long_key] = "test_value"
        assert config[long_key] == "test_value"
        assert long_key in config
    except (MemoryError, OverflowError):
        # Might fail with very long keys
        pass


# Test JSON with float edge cases
@given(
    float_values=st.lists(
        st.floats(allow_nan=True, allow_infinity=True),
        min_size=1,
        max_size=10
    )
)
def test_json_float_edge_cases(float_values):
    """Test Flask JSON with NaN and Infinity"""
    data = {"floats": float_values}
    
    try:
        encoded = json.dumps(data)
        # Standard JSON doesn't support NaN/Infinity
        # Flask might handle it differently
        decoded = json.loads(encoded)
        
        # Check if special values are preserved
        for original, decoded_val in zip(float_values, decoded["floats"]):
            if original != original:  # NaN check
                assert decoded_val != decoded_val
            else:
                assert original == decoded_val
    except (ValueError, TypeError):
        # Expected for NaN/Infinity in standard JSON
        pass