#!/usr/bin/env python3
"""Property-based tests for the yq module using Hypothesis."""

import json
import io
from datetime import datetime, date, time
from hypothesis import given, strategies as st, assume, settings
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/yq_env/lib/python3.13/site-packages')

import yq
from yq import JSONDateTimeEncoder, decode_docs
from yq.loader import hash_key


# Test 1: JSONDateTimeEncoder round-trip property
@given(
    st.datetimes(min_value=datetime(1900, 1, 1), max_value=datetime(2100, 1, 1))
)
def test_datetime_encoder_isoformat(dt):
    """Test that JSONDateTimeEncoder correctly encodes datetime to ISO format."""
    encoder = JSONDateTimeEncoder()
    encoded = encoder.default(dt)
    assert encoded == dt.isoformat()
    # Verify it's a valid ISO string that can be parsed back
    from datetime import datetime as dt_module
    parsed = dt_module.fromisoformat(encoded)
    # Check the essential parts match (ignore microseconds precision issues)
    assert parsed.year == dt.year
    assert parsed.month == dt.month
    assert parsed.day == dt.day
    assert parsed.hour == dt.hour
    assert parsed.minute == dt.minute


@given(st.dates(min_year=1900, max_year=2100))
def test_date_encoder_isoformat(d):
    """Test that JSONDateTimeEncoder correctly encodes date to ISO format."""
    encoder = JSONDateTimeEncoder()
    encoded = encoder.default(d)
    assert encoded == d.isoformat()
    from datetime import date as date_module
    parsed = date_module.fromisoformat(encoded)
    assert parsed == d


@given(st.times())
def test_time_encoder_isoformat(t):
    """Test that JSONDateTimeEncoder correctly encodes time to ISO format."""
    encoder = JSONDateTimeEncoder()
    encoded = encoder.default(t)
    assert encoded == t.isoformat()
    from datetime import time as time_module
    # Parse back and compare
    parsed = time_module.fromisoformat(encoded)
    assert parsed == t


# Test 2: decode_docs property - should handle multiple JSON documents
@given(
    st.lists(
        st.dictionaries(
            st.text(min_size=1, max_size=10),
            st.one_of(
                st.integers(),
                st.floats(allow_nan=False, allow_infinity=False),
                st.text(),
                st.booleans(),
                st.none()
            )
        ),
        min_size=1,
        max_size=5
    )
)
def test_decode_docs_multiple_documents(docs):
    """Test that decode_docs correctly parses multiple JSON documents."""
    # Encode documents to JSON string with newline separation
    jq_output = ""
    for doc in docs:
        jq_output += json.dumps(doc) + "\n"
    
    # Decode and verify
    decoder = json.JSONDecoder()
    decoded = list(decode_docs(jq_output, decoder))
    
    assert len(decoded) == len(docs)
    for original, decoded_doc in zip(docs, decoded):
        assert decoded_doc == original


# Test 3: decode_docs with various whitespace patterns
@given(
    st.dictionaries(
        st.text(min_size=1, max_size=5),
        st.integers()
    ),
    st.integers(min_value=0, max_value=10)  # whitespace count
)
def test_decode_docs_whitespace_handling(doc, whitespace_count):
    """Test that decode_docs handles various whitespace between documents."""
    jq_output = json.dumps(doc)
    # Add variable whitespace after document
    jq_output += " " * whitespace_count + "\n"
    
    decoder = json.JSONDecoder()
    decoded = list(decode_docs(jq_output, decoder))
    
    assert len(decoded) == 1
    assert decoded[0] == doc


# Test 4: hash_key consistency property
@given(st.text())
def test_hash_key_string_consistency(key):
    """Test that hash_key produces consistent output for string inputs."""
    hash1 = hash_key(key)
    hash2 = hash_key(key)
    assert hash1 == hash2
    # Verify it's base64 encoded
    import base64
    try:
        base64.b64decode(hash1)
    except Exception:
        assert False, "hash_key should produce valid base64"


@given(st.binary())
def test_hash_key_bytes_consistency(key):
    """Test that hash_key produces consistent output for bytes inputs."""
    hash1 = hash_key(key)
    hash2 = hash_key(key)
    assert hash1 == hash2
    # Verify it's base64 encoded
    import base64
    try:
        base64.b64decode(hash1)
    except Exception:
        assert False, "hash_key should produce valid base64"


# Test 5: hash_key different inputs produce different hashes (with high probability)
@given(
    st.text(min_size=1),
    st.text(min_size=1)
)
def test_hash_key_collision_resistance(key1, key2):
    """Test that different keys produce different hashes (collision resistance)."""
    assume(key1 != key2)
    hash1 = hash_key(key1)
    hash2 = hash_key(key2)
    # SHA-224 should have very low collision probability
    assert hash1 != hash2


# Test 6: decode_docs edge cases
def test_decode_docs_empty_string():
    """Test decode_docs with empty input."""
    decoder = json.JSONDecoder()
    result = list(decode_docs("", decoder))
    assert result == []


def test_decode_docs_whitespace_only():
    """Test decode_docs with whitespace-only input."""
    decoder = json.JSONDecoder()
    result = list(decode_docs("   \n  \t  ", decoder))
    assert result == []


# Test 7: JSONDateTimeEncoder with non-datetime types should raise
@given(
    st.one_of(
        st.dictionaries(st.text(), st.integers()),
        st.lists(st.integers()),
        st.text(),
        st.integers()
    )
)
def test_datetime_encoder_non_datetime_raises(obj):
    """Test that JSONDateTimeEncoder raises for non-datetime objects."""
    encoder = JSONDateTimeEncoder()
    try:
        result = encoder.default(obj)
        # If it doesn't raise, it should call the parent's default which raises
        assert False, "Should have raised TypeError"
    except TypeError:
        pass  # Expected behavior


if __name__ == "__main__":
    # Run with increased examples for thorough testing
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])