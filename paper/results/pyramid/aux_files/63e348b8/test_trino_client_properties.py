"""Property-based tests for trino.client module using Hypothesis."""

import base64
import math
import urllib.parse
from datetime import datetime, timedelta
from email.utils import format_datetime
from typing import Tuple, List

import pytest
from hypothesis import assume, given, strategies as st, settings
from hypothesis.strategies import composite

# Import the modules we're testing
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/trino_env/lib/python3.13/site-packages')

import trino.client as client
from trino.client import (
    get_header_values,
    get_session_property_values,
    get_roles_values,
    _DelayExponential,
    _parse_retry_after_header,
    InlineSegment,
    ClientSession,
    ROLE_PATTERN,
    _HEADER_EXTRA_CREDENTIAL_KEY_REGEX
)


# Strategy for valid header values (no control characters)
@composite
def header_value_strategy(draw):
    """Generate valid header values without control characters."""
    # Generate printable ASCII without control chars or commas
    chars = st.characters(min_codepoint=33, max_codepoint=126, blacklist_characters=',')
    return draw(st.text(alphabet=chars, min_size=1, max_size=100))


@composite  
def key_value_pair_strategy(draw):
    """Generate valid key=value pairs for headers."""
    # Keys should not contain '=' or whitespace
    key = draw(st.text(alphabet=st.characters(min_codepoint=33, max_codepoint=126, blacklist_characters='=, '), 
                       min_size=1, max_size=50))
    # Values can be any printable ASCII (will be URL encoded)
    value = draw(st.text(min_size=0, max_size=100))
    return key, value


# Test 1: URL encoding round-trip property
@given(st.text(min_size=0, max_size=200))
def test_url_encoding_round_trip(text):
    """Test that URL encoding and decoding is a perfect round-trip."""
    encoded = urllib.parse.quote_plus(text)
    decoded = urllib.parse.unquote_plus(encoded)
    assert decoded == text


# Test 2: Session property parsing round-trip
@given(st.lists(key_value_pair_strategy(), min_size=0, max_size=10))
def test_session_property_parsing_round_trip(pairs):
    """Test that session properties can be encoded and decoded correctly."""
    # Create header value
    header_value = ",".join(f"{k}={urllib.parse.quote_plus(v)}" for k, v in pairs)
    
    # Parse it back
    parsed = get_session_property_values(
        {'X-Test-Header': header_value}, 
        'X-Test-Header'
    )
    
    # Should get back the same pairs
    assert len(parsed) == len(pairs)
    for i, (key, value) in enumerate(pairs):
        assert parsed[i] == (key, value)


# Test 3: Header values parsing
@given(st.lists(header_value_strategy(), min_size=0, max_size=10))
def test_header_values_parsing(values):
    """Test that comma-separated header values are parsed correctly."""
    header_value = ", ".join(values)
    parsed = get_header_values({'X-Test': header_value}, 'X-Test')
    
    # Should get back the same values (stripped)
    assert len(parsed) == len(values)
    for i, value in enumerate(values):
        assert parsed[i] == value.strip()


# Test 4: Base64 encoding round-trip in InlineSegment
@given(st.binary(min_size=0, max_size=10000))
def test_inline_segment_base64_round_trip(data):
    """Test that InlineSegment correctly encodes/decodes base64 data."""
    # Encode the data as base64 (what the server would send)
    encoded = base64.b64encode(data).decode('utf-8')
    
    # Create an inline segment
    segment_data = {
        "type": "inline",
        "data": encoded,
        "metadata": {"segmentSize": str(len(data))}
    }
    
    segment = InlineSegment(segment_data)
    
    # The data property should decode back to original
    assert segment.data == data


# Test 5: Exponential backoff properties
@given(
    st.integers(min_value=0, max_value=100),  # attempt number
    st.floats(min_value=0.01, max_value=10),  # base
    st.integers(min_value=2, max_value=10),    # exponent
    st.floats(min_value=1, max_value=3600)     # max_delay
)
def test_exponential_backoff_max_delay(attempt, base, exponent, max_delay):
    """Test that exponential backoff respects max_delay."""
    delay_calc = _DelayExponential(base=base, exponent=exponent, jitter=False, max_delay=max_delay)
    delay = delay_calc(attempt)
    
    # Delay should never exceed max_delay
    assert delay <= max_delay
    
    # Without jitter, delay should be deterministic
    expected = min(base * (exponent ** attempt), max_delay)
    assert math.isclose(delay, expected, rel_tol=1e-9)


@given(
    st.integers(min_value=0, max_value=20),
    st.floats(min_value=0.01, max_value=1),
    st.integers(min_value=2, max_value=5)
)
def test_exponential_backoff_with_jitter(attempt, base, exponent):
    """Test that jitter keeps delay within expected bounds."""
    delay_calc = _DelayExponential(base=base, exponent=exponent, jitter=True, max_delay=3600)
    delay = delay_calc(attempt)
    
    # With jitter, delay should be between 0 and base * exponent^attempt
    max_expected = base * (exponent ** attempt)
    assert 0 <= delay <= min(max_expected, 3600)


# Test 6: Retry-after header parsing
@given(st.integers(min_value=0, max_value=86400))
def test_parse_retry_after_integer(seconds):
    """Test parsing integer retry-after values."""
    result = _parse_retry_after_header(seconds)
    assert result == seconds
    
    # Also test string representation
    result_str = _parse_retry_after_header(str(seconds))
    assert result_str == seconds


@given(st.datetimes(min_value=datetime.now() + timedelta(seconds=1),
                    max_value=datetime.now() + timedelta(days=1)))
def test_parse_retry_after_date(future_date):
    """Test parsing HTTP date format retry-after values."""
    # Format as HTTP date
    http_date = format_datetime(future_date, usegmt=True)
    
    # Parse it
    result = _parse_retry_after_header(http_date)
    
    # Should be positive (in the future)
    assert result > 0
    # Should be less than a day + some buffer for test execution time
    assert result < 86400 + 60


# Test 7: Extra credential validation
@given(st.text(alphabet=st.characters(min_codepoint=33, max_codepoint=126, blacklist_characters='= '), 
               min_size=1, max_size=50))
def test_valid_extra_credential_key(key):
    """Test that valid extra credential keys pass validation."""
    # Should not raise for valid ASCII keys without whitespace or '='
    try:
        client.TrinoRequest._verify_extra_credential((key, "some_value"))
        # If no exception, the test passes
    except ValueError:
        # Check if the key actually violates the rules
        if not _HEADER_EXTRA_CREDENTIAL_KEY_REGEX.match(key):
            # Expected to fail
            pass
        else:
            # Should not have failed
            raise


@given(st.text(min_size=1, max_size=50))
def test_extra_credential_validation_rules(key):
    """Test extra credential validation catches invalid keys."""
    value = "test_value"
    
    should_fail = False
    # Check if key has whitespace or equals
    if ' ' in key or '=' in key or '\t' in key or '\n' in key or '\r' in key:
        should_fail = True
    # Check if key has leading/trailing whitespace
    if key != key.strip():
        should_fail = True
    # Check if key is empty after stripping
    if not key.strip():
        should_fail = True
    # Check if key has non-ASCII characters
    try:
        key.encode('ascii')
    except UnicodeEncodeError:
        should_fail = True
    
    if should_fail:
        with pytest.raises(ValueError):
            client.TrinoRequest._verify_extra_credential((key, value))
    else:
        # For valid keys, check they match the regex
        if _HEADER_EXTRA_CREDENTIAL_KEY_REGEX.match(key):
            # Should not raise
            client.TrinoRequest._verify_extra_credential((key, value))


# Test 8: Role formatting
@given(st.dictionaries(
    st.text(alphabet=st.characters(min_codepoint=65, max_codepoint=122), min_size=1, max_size=20),
    st.text(alphabet=st.characters(min_codepoint=65, max_codepoint=122), min_size=1, max_size=50)
))
def test_client_session_role_formatting(roles):
    """Test that ClientSession formats roles correctly."""
    formatted = ClientSession._format_roles(roles)
    
    for catalog, role in roles.items():
        if role in ("NONE", "ALL"):
            # These special values should be kept as-is
            assert formatted[catalog] == role
        elif ROLE_PATTERN.match(role):
            # Already in ROLE{} format (legacy)
            assert formatted[catalog] == role
        else:
            # Should be wrapped in ROLE{}
            assert formatted[catalog] == f"ROLE{{{role}}}"


# Test 9: ClientSession with single string role
@given(st.text(alphabet=st.characters(min_codepoint=65, max_codepoint=122), min_size=1, max_size=50))
def test_client_session_single_role_formatting(role):
    """Test that ClientSession handles single role strings correctly."""
    formatted = ClientSession._format_roles(role)
    
    # Single string role should be assigned to "system" catalog
    assert "system" in formatted
    
    if role in ("NONE", "ALL"):
        assert formatted["system"] == role
    elif ROLE_PATTERN.match(role):
        assert formatted["system"] == role
    else:
        assert formatted["system"] == f"ROLE{{{role}}}"


# Test 10: InlineSegment metadata property
@given(
    st.binary(min_size=0, max_size=1000),
    st.dictionaries(st.text(min_size=1, max_size=20), st.text(min_size=1, max_size=100))
)
def test_inline_segment_metadata(data, metadata):
    """Test that InlineSegment preserves metadata correctly."""
    encoded = base64.b64encode(data).decode('utf-8')
    segment_data = {
        "type": "inline", 
        "data": encoded,
        "metadata": metadata
    }
    
    segment = InlineSegment(segment_data)
    
    # Metadata should be preserved
    assert segment.metadata == metadata


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])