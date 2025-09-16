#!/usr/bin/env python3
"""Property-based tests for pyatlan.test_utils module"""

import json
import sys
import os
from hypothesis import assume, given, strategies as st, settings

# Add the site-packages to Python path
sys.path.insert(0, '/root/hypothesis-llm/envs/pyatlan_env/lib/python3.13/site-packages')

from pyatlan.test_utils import TestId
from pyatlan.test_utils.base_vcr import (
    process_string_value,
    VCRPrettyPrintJSONBody,
    LiteralBlockScalar,
)


# Test 1: TestId.make_unique properties
@given(st.text(min_size=1, max_size=100))
def test_make_unique_format(input_text):
    """Test that make_unique always produces correctly formatted output"""
    # Skip inputs with control characters that might break formatting
    assume(all(ord(c) >= 32 or c in '\t\n\r' for c in input_text))
    
    result = TestId.make_unique(input_text)
    
    # Property 1: Output starts with "psdk_"
    assert result.startswith("psdk_"), f"Expected to start with 'psdk_', got: {result}"
    
    # Property 2: Output contains the input string
    assert input_text in result, f"Expected {input_text} in {result}"
    
    # Property 3: Output ends with the session_id
    assert result.endswith(TestId.session_id), f"Expected to end with {TestId.session_id}, got: {result}"
    
    # Property 4: Format is exactly "psdk_{input}_{session_id}"
    expected = f"psdk_{input_text}_{TestId.session_id}"
    assert result == expected, f"Expected {expected}, got {result}"


@given(st.text(min_size=1, max_size=100))
def test_make_unique_idempotent(input_text):
    """Test that make_unique is idempotent within a session"""
    assume(all(ord(c) >= 32 or c in '\t\n\r' for c in input_text))
    
    result1 = TestId.make_unique(input_text)
    result2 = TestId.make_unique(input_text)
    
    # Same input should produce same output
    assert result1 == result2, f"Not idempotent: {result1} != {result2}"


# Test 2: process_string_value properties
@given(st.text(min_size=1))
def test_process_string_value_json_vs_plain(text):
    """Test process_string_value correctly handles JSON vs plain text"""
    result = process_string_value(text)
    
    # Try to parse as JSON
    try:
        json.loads(text)
        is_json = True
    except (ValueError, TypeError):
        is_json = False
    
    if is_json:
        # For valid JSON, should return as LiteralBlockScalar with pretty-printed JSON
        assert isinstance(result, LiteralBlockScalar)
        # Verify it's pretty-printed (has indentation)
        parsed = json.loads(text)
        expected = json.dumps(parsed, indent=2)
        assert str(result) == expected
    else:
        # For non-JSON strings
        if len(text) > 80:
            # Long strings should be LiteralBlockScalar
            assert isinstance(result, LiteralBlockScalar)
            assert str(result) == text
        else:
            # Short strings should be unchanged
            assert result == text
            assert not isinstance(result, LiteralBlockScalar)


# Test 3: VCRPrettyPrintJSONBody._parse_json_body properties
@given(st.one_of(
    st.none(),
    st.binary(),
    st.text()
))
def test_parse_json_body_types(body):
    """Test _parse_json_body handles different input types correctly"""
    result = VCRPrettyPrintJSONBody._parse_json_body(body)
    
    if body is None:
        assert result is None
    elif isinstance(body, bytes):
        try:
            decoded = body.decode('utf-8')
            try:
                parsed = json.loads(decoded)
                assert result == parsed
            except json.JSONDecodeError:
                assert result == decoded
        except UnicodeDecodeError:
            assert result == body  # Should return original bytes
    elif isinstance(body, str):
        try:
            parsed = json.loads(body)
            assert result == parsed
        except json.JSONDecodeError:
            assert result == body


# Test 4: Round-trip property for JSON data
@given(st.recursive(
    st.one_of(
        st.none(),
        st.booleans(),
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.text()
    ),
    lambda children: st.one_of(
        st.lists(children, max_size=10),
        st.dictionaries(st.text(), children, max_size=10)
    ),
    max_leaves=50
))
def test_vcr_json_round_trip(json_data):
    """Test VCRPrettyPrintJSONBody serialize/deserialize round-trip for JSON data"""
    # Create a minimal cassette structure with JSON body
    cassette = {
        "interactions": [{
            "request": {
                "body": {"string": json.dumps(json_data)}
            },
            "response": {
                "body": {"string": json.dumps(json_data)}
            }
        }]
    }
    
    # Serialize and deserialize
    serialized = VCRPrettyPrintJSONBody.serialize(cassette)
    deserialized = VCRPrettyPrintJSONBody.deserialize(serialized)
    
    # Check that we get back equivalent data
    assert "interactions" in deserialized
    assert len(deserialized["interactions"]) == 1
    
    interaction = deserialized["interactions"][0]
    
    # Check request body
    req_body = interaction["request"]["body"]["string"]
    req_data = json.loads(req_body)
    assert req_data == json_data
    
    # Check response body
    resp_body = interaction["response"]["body"]["string"]
    resp_data = json.loads(resp_body)
    assert resp_data == json_data


# Test 5: Edge cases for empty/malformed cassettes
@given(st.one_of(
    st.none(),
    st.text(),
    st.dictionaries(st.text(), st.text(), max_size=5)
))
def test_vcr_json_serialize_safety(cassette_dict):
    """Test VCRPrettyPrintJSONBody.serialize handles edge cases safely"""
    # Should not crash on any input
    result = VCRPrettyPrintJSONBody.serialize(cassette_dict)
    assert isinstance(result, str)
    
    # Should be valid JSON
    if result.strip():  # Skip empty results
        parsed = json.loads(result)
        assert isinstance(parsed, dict)


@given(st.text())
def test_vcr_json_deserialize_safety(cassette_string):
    """Test VCRPrettyPrintJSONBody.deserialize handles edge cases safely"""
    # Should not crash on any input
    result = VCRPrettyPrintJSONBody.deserialize(cassette_string)
    assert isinstance(result, dict)
    
    # Valid JSON should parse correctly
    if cassette_string.strip():
        try:
            json.loads(cassette_string)
            # If it's valid JSON, result should have content
            assert result != {} or cassette_string.strip() == "{}"
        except json.JSONDecodeError:
            # Invalid JSON should return empty dict
            assert result == {}


if __name__ == "__main__":
    # Run with increased examples for better bug hunting
    import pytest
    
    # Run the tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])