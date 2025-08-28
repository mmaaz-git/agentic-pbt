import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/aws-lambda-powertools_env/lib/python3.13/site-packages')

import base64
import gzip
import json
from hypothesis import given, strategies as st, assume, settings, example
import pytest

from aws_lambda_powertools.utilities.serialization import (
    base64_encode,
    base64_decode,
    base64_from_str,
    base64_from_json
)
from aws_lambda_powertools.utilities.jmespath_utils import PowertoolsFunctions, query
from aws_lambda_powertools.exceptions import InvalidEnvelopeExpressionError


# Test with null bytes and control characters
@given(st.text(alphabet=st.characters(min_codepoint=0, max_codepoint=127)))
def test_base64_with_control_characters(text):
    """Test base64 encoding/decoding with control characters including null bytes"""
    encoded = base64_encode(text)
    decoded = base64_decode(encoded)
    assert decoded == text


# Test with invalid base64 input
@given(st.text(alphabet='!@#$%^&*()[]{}|\\:;"\'<>,.?/~`', min_size=1))
def test_base64_decode_invalid_input(invalid_text):
    """Test that invalid base64 input raises appropriate errors"""
    # Most non-base64 characters should cause decoding errors
    assume(len(invalid_text) > 0)
    try:
        decoded = base64_decode(invalid_text)
        # If it doesn't raise an error, it should at least not crash
    except Exception as e:
        # Should raise a specific base64 error
        assert isinstance(e, (ValueError, base64.binascii.Error))


# Test JSON with NaN and Infinity
def test_base64_from_json_with_special_floats():
    """Test that JSON encoding handles special float values"""
    # JSON standard doesn't support NaN/Infinity
    import math
    
    # These should fail during JSON serialization
    with pytest.raises(ValueError):
        base64_from_json(float('nan'))
    
    with pytest.raises(ValueError):
        base64_from_json(float('inf'))
    
    with pytest.raises(ValueError):
        base64_from_json(float('-inf'))


# Test deeply nested structures
@given(
    st.recursive(
        st.one_of(st.integers(), st.text(max_size=10)),
        lambda children: st.lists(children, min_size=1, max_size=3) | 
                        st.dictionaries(st.text(min_size=1, max_size=3), children, min_size=1, max_size=3),
        max_leaves=100
    )
)
@settings(max_examples=50)
def test_base64_from_json_deeply_nested(data):
    """Test JSON encoding with deeply nested structures"""
    encoded = base64_from_json(data)
    decoded_str = base64.b64decode(encoded).decode('utf-8')
    decoded_data = json.loads(decoded_str)
    assert decoded_data == data


# Test JMESPath query function
@given(
    st.dictionaries(
        st.text(min_size=1, max_size=10),
        st.one_of(st.integers(), st.text(), st.booleans(), st.none())
    )
)
def test_jmespath_query_basic(data):
    """Test basic JMESPath query functionality"""
    # Test that we can query keys that exist
    for key in data.keys():
        result = query(data, key)
        assert result == data[key]


# Test powertools_json function through query
@given(
    st.one_of(
        st.dictionaries(st.text(min_size=1), st.integers()),
        st.lists(st.integers()),
        st.text(),
        st.integers(),
        st.booleans(),
        st.none()
    )
)
def test_query_powertools_json(data):
    """Test the powertools_json JMESPath function"""
    json_str = json.dumps(data)
    wrapper = {"payload": json_str}
    
    result = query(wrapper, "powertools_json(payload)")
    assert result == data


# Test powertools_base64 function through query
@given(st.text())
def test_query_powertools_base64(text):
    """Test the powertools_base64 JMESPath function"""
    encoded = base64.b64encode(text.encode()).decode()
    wrapper = {"encoded": encoded}
    
    result = query(wrapper, "powertools_base64(encoded)")
    assert result == text


# Test powertools_base64_gzip function through query
@given(st.text())
def test_query_powertools_base64_gzip(text):
    """Test the powertools_base64_gzip JMESPath function"""
    compressed = gzip.compress(text.encode())
    encoded = base64.b64encode(compressed).decode()
    wrapper = {"compressed": encoded}
    
    result = query(wrapper, "powertools_base64_gzip(compressed)")
    assert result == text


# Test invalid JMESPath expressions
@given(st.text(alphabet='!@#$%^&*()[]{}|\\', min_size=5, max_size=20))
def test_query_invalid_expression(invalid_expr):
    """Test that invalid JMESPath expressions raise appropriate errors"""
    data = {"test": "value"}
    
    # Many special characters will create invalid JMESPath expressions
    try:
        result = query(data, invalid_expr)
    except InvalidEnvelopeExpressionError:
        # This is expected for invalid expressions
        pass
    except Exception as e:
        # Should only raise InvalidEnvelopeExpressionError for bad expressions
        pytest.fail(f"Unexpected exception type: {type(e)}")


# Test with very long strings (might hit memory or performance issues)
@given(st.text(alphabet=st.characters(min_codepoint=32, max_codepoint=126), min_size=5000, max_size=8000))
@settings(max_examples=5)
def test_base64_very_long_strings(long_text):
    """Test with very long strings to check for buffer or memory issues"""
    encoded = base64_encode(long_text)
    decoded = base64_decode(encoded)
    assert decoded == long_text
    assert len(encoded) > len(long_text)  # Base64 is larger


# Test base64_decode with strings that are not properly padded
def test_base64_decode_padding_issues():
    """Test base64 decoding with improper padding"""
    # Valid base64 but missing padding
    test_cases = [
        "SGVsbG8",      # Should be "SGVsbG8=" for "Hello"
        "SGVsbG8gV29ybGQ",  # Should have padding
        "YQ",           # Should be "YQ==" for "a"
        "YWI"           # Should be "YWI=" for "ab"
    ]
    
    for test_case in test_cases:
        try:
            decoded = base64_decode(test_case)
            # Python's base64 might handle missing padding gracefully
            # If it does, verify it decodes correctly
            re_encoded = base64_encode(decoded)
            # The re-encoded version should have proper padding
        except Exception as e:
            # If it raises an error, it should be a padding error
            assert "padding" in str(e).lower() or isinstance(e, base64.binascii.Error)


# Test with byte sequences that might not be valid UTF-8 when decoded
def test_base64_decode_non_utf8():
    """Test decoding base64 that doesn't represent valid UTF-8"""
    # Create base64 that when decoded is not valid UTF-8
    invalid_utf8 = b'\xff\xfe\xfd'
    encoded = base64.b64encode(invalid_utf8).decode('ascii')
    
    # This should raise a UnicodeDecodeError
    with pytest.raises(UnicodeDecodeError):
        base64_decode(encoded)


# Test extreme recursion in JSON
def test_json_extreme_recursion():
    """Test JSON encoding with extreme recursion depth"""
    # Create a deeply nested structure
    data = {"level": 0}
    current = data
    for i in range(100):
        current["next"] = {"level": i + 1}
        current = current["next"]
    
    # This should work fine
    encoded = base64_from_json(data)
    decoded_str = base64.b64decode(encoded).decode('utf-8')
    decoded_data = json.loads(decoded_str)
    
    # Verify structure is preserved
    current = decoded_data
    for i in range(101):
        assert current["level"] == i
        if i < 100:
            current = current["next"]