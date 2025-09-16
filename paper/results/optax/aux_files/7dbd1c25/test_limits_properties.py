#!/usr/bin/env /root/hypothesis-llm/envs/limits_env/bin/python3
"""Property-based tests for limits.limits module"""

import math
from hypothesis import assume, given, strategies as st, settings
from hypothesis.strategies import composite
import limits.limits as ll
from limits import parse, parse_many
from limits.limits import (
    RateLimitItem,
    RateLimitItemPerSecond,
    RateLimitItemPerMinute,
    RateLimitItemPerHour,
    RateLimitItemPerDay,
    RateLimitItemPerMonth,
    RateLimitItemPerYear,
    safe_string,
    TIME_TYPES,
)


# Strategy for generating rate limit classes
rate_limit_classes = st.sampled_from([
    RateLimitItemPerSecond,
    RateLimitItemPerMinute,
    RateLimitItemPerHour,
    RateLimitItemPerDay,
    RateLimitItemPerMonth,
    RateLimitItemPerYear,
])

# Strategy for generating valid rate limit items
@composite
def rate_limit_items(draw):
    cls = draw(rate_limit_classes)
    amount = draw(st.integers(min_value=1, max_value=10000))
    multiples = draw(st.integers(min_value=1, max_value=100))
    namespace = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(min_codepoint=65, max_codepoint=122)))
    return cls(amount=amount, multiples=multiples, namespace=namespace)


# Test 1: Ordering transitivity
@given(rate_limit_items(), rate_limit_items(), rate_limit_items())
def test_ordering_transitivity(a, b, c):
    """Test that ordering is transitive: if a < b and b < c, then a < c"""
    if a < b and b < c:
        assert a < c
    if a <= b and b <= c:
        assert a <= c
    if a > b and b > c:
        assert a > c
    if a >= b and b >= c:
        assert a >= c


# Test 2: Equality and hash consistency
@given(rate_limit_items())
def test_equality_hash_consistency(item):
    """Test that equal objects have equal hashes"""
    # Create an identical item
    same_item = type(item)(
        amount=item.amount,
        multiples=item.multiples,
        namespace=item.namespace
    )
    assert item == same_item
    assert hash(item) == hash(same_item)


# Test 3: Key generation invariants
@given(rate_limit_items(), st.lists(st.one_of(
    st.text(min_size=0, max_size=100),
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.binary(min_size=0, max_size=100)
), min_size=0, max_size=5))
def test_key_generation_structure(item, identifiers):
    """Test that key_for generates keys with expected structure"""
    key = item.key_for(*identifiers)
    
    # Key should be a string
    assert isinstance(key, str)
    
    # Key should start with namespace
    assert key.startswith(item.namespace + "/")
    
    # Key should contain amount, multiples, and granularity name
    assert str(item.amount) in key
    assert str(item.multiples) in key
    assert item.GRANULARITY.name in key
    
    # Key should use '/' as delimiter
    parts = key.split('/')
    assert len(parts) >= 4  # namespace, [identifiers...], amount, multiples, granularity


# Test 4: Safe string conversion never fails
@given(st.one_of(
    st.binary(),
    st.text(),
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False)
))
def test_safe_string_never_fails(value):
    """Test that safe_string handles all expected input types"""
    result = safe_string(value)
    assert isinstance(result, str)
    
    # Specific checks for bytes
    if isinstance(value, bytes):
        try:
            expected = value.decode()
            assert result == expected
        except UnicodeDecodeError:
            # If bytes can't be decoded, safe_string should still return something
            pass


# Test 5: Expiry calculation correctness
@given(rate_limit_items())
def test_expiry_calculation(item):
    """Test that get_expiry returns the correct duration"""
    expected = item.GRANULARITY.seconds * item.multiples
    assert item.get_expiry() == expected


# Test 6: Parse and parse_many relationship
@given(st.sampled_from([
    "1/second",
    "5/minute",
    "10/hour",
    "100/day",
    "1 per second",
    "5 per minute",
    "10 per hour",
    "100 per day",
    "2/5/seconds",
    "3/10/minutes",
]))
def test_parse_parse_many_relationship(limit_string):
    """Test that parse(s) equals parse_many(s)[0] for single limits"""
    single = parse(limit_string)
    many = parse_many(limit_string)
    
    assert len(many) == 1
    assert many[0].amount == single.amount
    assert many[0].multiples == single.multiples
    assert many[0].GRANULARITY == single.GRANULARITY


# Test 7: Granularity string checking accepts plurals
@given(rate_limit_classes)
def test_granularity_string_plural_forms(cls):
    """Test that check_granularity_string accepts both singular and plural"""
    singular = cls.GRANULARITY.name
    plural = singular + "s"
    
    assert cls.check_granularity_string(singular)
    assert cls.check_granularity_string(plural)
    assert cls.check_granularity_string(singular.upper())
    assert cls.check_granularity_string(plural.upper())


# Test 8: Round-trip through string representation
@given(
    st.integers(min_value=1, max_value=1000),
    st.integers(min_value=1, max_value=100),
    st.sampled_from(["second", "minute", "hour", "day", "month", "year"])
)
def test_parse_representation_round_trip(amount, multiples, granularity):
    """Test round-trip: create -> represent -> parse"""
    # Build the string
    if multiples == 1:
        limit_string = f"{amount}/{granularity}"
    else:
        limit_string = f"{amount}/{multiples}/{granularity}"
    
    # Parse it
    parsed = parse(limit_string)
    
    # Check the parsed values
    assert parsed.amount == amount
    assert parsed.multiples == multiples
    assert parsed.GRANULARITY.name == granularity


# Test 9: Multiple limits parsing
@given(st.lists(
    st.tuples(
        st.integers(min_value=1, max_value=100),
        st.integers(min_value=1, max_value=10),
        st.sampled_from(["second", "minute", "hour", "day"])
    ),
    min_size=2,
    max_size=5
))
def test_parse_many_multiple_limits(limits_data):
    """Test parsing multiple rate limits separated by semicolons"""
    # Build the string
    parts = []
    for amount, multiples, granularity in limits_data:
        if multiples == 1:
            parts.append(f"{amount}/{granularity}")
        else:
            parts.append(f"{amount}/{multiples}/{granularity}")
    
    limit_string = "; ".join(parts)
    
    # Parse it
    parsed = parse_many(limit_string)
    
    # Verify we got the right number of limits
    assert len(parsed) == len(limits_data)
    
    # Verify each limit
    for (amount, multiples, granularity), parsed_item in zip(limits_data, parsed):
        assert parsed_item.amount == amount
        assert parsed_item.multiples == multiples
        assert parsed_item.GRANULARITY.name == granularity


# Test 10: Inequality and equality are consistent
@given(rate_limit_items(), rate_limit_items())
def test_equality_inequality_consistency(a, b):
    """Test that == and != are consistent"""
    if a == b:
        assert not (a != b)
        assert hash(a) == hash(b)
    else:
        assert a != b


# Test 11: __repr__ contains expected information
@given(rate_limit_items())
def test_repr_contains_info(item):
    """Test that __repr__ contains the expected information"""
    repr_str = repr(item)
    assert str(item.amount) in repr_str
    assert str(item.multiples) in repr_str
    assert item.GRANULARITY.name in repr_str


# Test 12: Test with edge case for safe_string with various byte encodings
@given(st.text())
def test_safe_string_bytes_encoding(text):
    """Test safe_string with various byte encodings"""
    # Try different encodings
    for encoding in ['utf-8', 'latin-1', 'ascii']:
        try:
            byte_value = text.encode(encoding)
            result = safe_string(byte_value)
            assert isinstance(result, str)
            # For valid utf-8, should decode correctly
            if encoding == 'utf-8':
                assert result == text
        except (UnicodeEncodeError, UnicodeDecodeError):
            # Some text might not be encodable in certain encodings
            pass


if __name__ == "__main__":
    # Run with pytest
    import sys
    import subprocess
    result = subprocess.run([sys.executable, "-m", "pytest", __file__, "-v", "--tb=short"])
    sys.exit(result.returncode)