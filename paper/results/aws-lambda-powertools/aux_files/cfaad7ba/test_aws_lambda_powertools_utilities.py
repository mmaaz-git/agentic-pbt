import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/aws-lambda-powertools_env/lib/python3.13/site-packages')

import base64
import gzip
import json
from hypothesis import given, strategies as st, assume, settings
import pytest

from aws_lambda_powertools.utilities.serialization import (
    base64_encode,
    base64_decode,
    base64_from_str,
    base64_from_json
)
from aws_lambda_powertools.utilities.jmespath_utils import PowertoolsFunctions


# Test 1: Base64 encode/decode round-trip property
@given(st.text())
def test_base64_round_trip(text):
    """Test that base64_decode(base64_encode(x)) == x for any string"""
    encoded = base64_encode(text)
    decoded = base64_decode(encoded)
    assert decoded == text, f"Round-trip failed for text: {repr(text)}"


# Test 2: base64_from_str should be equivalent to base64_encode
@given(st.text())
def test_base64_from_str_equals_base64_encode(text):
    """Test that base64_from_str and base64_encode produce the same result"""
    result1 = base64_encode(text)
    result2 = base64_from_str(text)
    assert result1 == result2, f"Functions produced different results for: {repr(text)}"


# Test 3: base64_from_json round-trip property
@given(
    st.one_of(
        st.none(),
        st.booleans(),
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.text(),
        st.lists(st.integers()),
        st.dictionaries(st.text(min_size=1), st.integers()),
        st.recursive(
            st.one_of(st.none(), st.booleans(), st.integers(), st.text()),
            lambda children: st.lists(children) | st.dictionaries(st.text(min_size=1), children),
            max_leaves=10
        )
    )
)
def test_base64_from_json_round_trip(data):
    """Test that we can encode JSON data to base64 and decode it back"""
    encoded = base64_from_json(data)
    # Decode base64 then parse JSON
    decoded_str = base64.b64decode(encoded).decode('utf-8')
    decoded_data = json.loads(decoded_str)
    assert decoded_data == data, f"Round-trip failed for data: {repr(data)}"


# Test 4: PowertoolsFunctions base64 decoding
@given(st.text())
def test_powertools_base64_function(text):
    """Test that PowertoolsFunctions._func_powertools_base64 correctly decodes base64"""
    funcs = PowertoolsFunctions()
    # Encode the text to base64
    encoded = base64.b64encode(text.encode()).decode()
    # Use the powertools function to decode
    decoded = funcs._func_powertools_base64(encoded)
    assert decoded == text, f"Decoding failed for text: {repr(text)}"


# Test 5: PowertoolsFunctions base64_gzip round-trip
@given(st.text())
def test_powertools_base64_gzip_round_trip(text):
    """Test that we can compress, base64 encode, then decode with powertools function"""
    funcs = PowertoolsFunctions()
    
    # Compress and base64 encode
    compressed = gzip.compress(text.encode())
    encoded = base64.b64encode(compressed).decode()
    
    # Use powertools function to decode
    decoded = funcs._func_powertools_base64_gzip(encoded)
    assert decoded == text, f"Round-trip failed for text: {repr(text)}"


# Test 6: PowertoolsFunctions JSON parsing
@given(
    st.one_of(
        st.none(),
        st.booleans(),
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.text(),
        st.lists(st.integers()),
        st.dictionaries(st.text(min_size=1), st.integers())
    )
)
def test_powertools_json_function(data):
    """Test that PowertoolsFunctions._func_powertools_json correctly parses JSON"""
    funcs = PowertoolsFunctions()
    json_str = json.dumps(data)
    parsed = funcs._func_powertools_json(json_str)
    assert parsed == data, f"JSON parsing failed for data: {repr(data)}"


# Test 7: Test edge cases with special characters
@given(
    st.text(
        alphabet=st.characters(
            whitelist_categories=("Nd", "Lu", "Ll", "Lt", "Lm", "Lo", "Nl", "Pc", "Pd", "Ps", "Pe", "Pi", "Pf", "Po", "Sm", "Sc", "Sk", "So", "Zs", "Zl", "Zp"),
            blacklist_characters="\x00"  # Null character often causes issues
        )
    )
)
def test_base64_with_unicode(text):
    """Test base64 encoding/decoding with various Unicode characters"""
    encoded = base64_encode(text)
    decoded = base64_decode(encoded)
    assert decoded == text, f"Unicode round-trip failed for text with {len(text)} chars"


# Test 8: Empty string edge case
def test_base64_empty_string():
    """Test that empty strings are handled correctly"""
    empty = ""
    encoded = base64_encode(empty)
    decoded = base64_decode(encoded)
    assert decoded == empty
    assert encoded == ""  # Empty string encodes to empty base64


# Test 9: Large data handling
@given(st.text(min_size=1000, max_size=5000))
@settings(max_examples=10)  # Reduce examples for performance
def test_base64_large_data(large_text):
    """Test that large strings are handled correctly"""
    encoded = base64_encode(large_text)
    decoded = base64_decode(encoded)
    assert decoded == large_text