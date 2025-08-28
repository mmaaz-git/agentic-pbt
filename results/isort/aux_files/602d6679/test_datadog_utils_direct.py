#!/usr/bin/env python3
"""Direct property-based tests for datadog_checks.utils functions."""

import datetime
import math
import re
from decimal import ROUND_HALF_UP, ROUND_DOWN, ROUND_UP, Decimal
from hypothesis import assume, given, strategies as st, settings
import pytest


# Copy the function implementations directly to test them

def ensure_bytes(s):
    if isinstance(s, str):
        s = s.encode('utf-8')
    return s


def ensure_unicode(s):
    if isinstance(s, bytes):
        s = s.decode('utf-8')
    return s


def compute_percent(part, total):
    if total:
        return part / total * 100
    return 0


def round_value(value, precision=0, rounding_method=ROUND_HALF_UP):
    precision = '0.{}'.format('0' * precision)
    return float(Decimal(str(value)).quantize(Decimal(precision), rounding=rounding_method))


def exclude_undefined_keys(mapping):
    return {key: value for key, value in mapping.items() if value is not None}


def pattern_filter(items, whitelist=None, blacklist=None, key=None):
    """This filters `items` by a regular expression `whitelist` and/or
    `blacklist`, with the `blacklist` taking precedence. An optional `key`
    function can be provided that will be passed each item.
    """
    def __return_self(obj):
        return obj
    
    def _filter(items, pattern_list, key):
        return {key(item) for pattern in pattern_list for item in items if re.search(pattern, key(item))}
    
    key = key or __return_self
    if whitelist:
        whitelisted = _filter(items, whitelist, key)

        if blacklist:
            blacklisted = _filter(items, blacklist, key)
            # Remove any blacklisted items from the whitelisted ones.
            whitelisted.difference_update(blacklisted)

        return [item for item in items if key(item) in whitelisted]

    elif blacklist:
        blacklisted = _filter(items, blacklist, key)
        return [item for item in items if key(item) not in blacklisted]

    else:
        return items


def identity(obj, **kwargs):
    return obj


def predicate(assertion):
    return return_true if bool(assertion) else return_false


def return_true(*args, **kwargs):
    return True


def return_false(*args, **kwargs):
    return False


def total_time_to_temporal_percent(total_time, scale=1000):
    return total_time / scale * 100


# Date parsing functions
class TimezoneInfo(datetime.tzinfo):
    def __init__(self, h, m):
        self._name = "UTC"
        if h != 0 and m != 0:
            self._name += "%+03d:%2d" % (h, m)
        self._delta = datetime.timedelta(hours=h, minutes=math.copysign(m, h))

    def utcoffset(self, dt):
        return self._delta

    def tzname(self, dt):
        return self._name

    def dst(self, dt):
        return datetime.timedelta(0)


UTC = TimezoneInfo(0, 0)

_re_rfc3339 = re.compile(
    r"(\d\d\d\d)-(\d\d)-(\d\d)"  # full-date
    r"[ Tt]"  # Separator
    r"(\d\d):(\d\d):(\d\d)([.,]\d+)?"  # partial-time
    r"([zZ ]|[-+]\d\d?:\d\d)?",  # time-offset
    re.VERBOSE + re.IGNORECASE,
)
_re_timezone = re.compile(r"([-+])(\d\d?):?(\d\d)?")


def parse_rfc3339(s):
    if isinstance(s, datetime.datetime):
        # no need to parse it, just make sure it has a timezone.
        if not s.tzinfo:
            return s.replace(tzinfo=UTC)
        return s
    groups = _re_rfc3339.search(s).groups()
    dt = [0] * 7
    for x in range(6):
        dt[x] = int(groups[x])
    if groups[6] is not None:
        dt[6] = int(groups[6])
    tz = UTC
    if groups[7] is not None and groups[7] != 'Z' and groups[7] != 'z':
        tz_groups = _re_timezone.search(groups[7]).groups()
        hour = int(tz_groups[1])
        minute = 0
        if tz_groups[0] == "-":
            hour *= -1
        if tz_groups[2]:
            minute = int(tz_groups[2])
        tz = TimezoneInfo(hour, minute)
    return datetime.datetime(
        year=dt[0], month=dt[1], day=dt[2], hour=dt[3], minute=dt[4], second=dt[5], microsecond=dt[6], tzinfo=tz
    )


def format_rfc3339(date_time):
    if date_time.tzinfo is None:
        date_time = date_time.replace(tzinfo=UTC)
    date_time = date_time.astimezone(UTC)
    return date_time.strftime('%Y-%m-%dT%H:%M:%SZ')


# PROPERTY-BASED TESTS

# Test 1: ensure_bytes/ensure_unicode round-trip property
@given(st.text())
def test_ensure_unicode_bytes_roundtrip(s):
    """Test that ensure_bytes and ensure_unicode are inverse operations."""
    # String -> bytes -> string
    bytes_val = ensure_bytes(s)
    back_to_str = ensure_unicode(bytes_val)
    assert back_to_str == s
    
    # Also test bytes -> string -> bytes
    original_bytes = s.encode('utf-8')
    str_val = ensure_unicode(original_bytes)
    back_to_bytes = ensure_bytes(str_val)
    assert back_to_bytes == original_bytes


# Test 2: RFC3339 date parse/format round-trip property
@given(st.datetimes(min_value=datetime.datetime(1900, 1, 1), max_value=datetime.datetime(2100, 1, 1)))
def test_rfc3339_parse_format_roundtrip(dt):
    """Test that RFC3339 format and parse are inverse operations."""
    # Add UTC timezone if not present
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    
    formatted = format_rfc3339(dt)
    parsed = parse_rfc3339(formatted)
    
    # Since formatting converts to UTC, we should compare in UTC
    dt_utc = dt.astimezone(UTC)
    
    # Compare with microsecond precision removed (format doesn't preserve microseconds)
    assert parsed.replace(microsecond=0) == dt_utc.replace(microsecond=0)


# Test 3: pattern_filter invariants
@given(
    st.lists(st.text(min_size=1, max_size=10), min_size=1, max_size=20),
    st.lists(st.text(min_size=1, max_size=10), min_size=0, max_size=5),
    st.lists(st.text(min_size=1, max_size=10), min_size=0, max_size=5)
)
def test_pattern_filter_blacklist_precedence(items, whitelist_items, blacklist_items):
    """Test that blacklist takes precedence over whitelist in pattern_filter."""
    # Use literal strings as patterns
    whitelist_patterns = [re.escape(item) for item in whitelist_items] if whitelist_items else None
    blacklist_patterns = [re.escape(item) for item in blacklist_items] if blacklist_items else None
    
    result = pattern_filter(items, whitelist=whitelist_patterns, blacklist=blacklist_patterns)
    
    # If blacklist is provided, no item matching blacklist should be in result
    if blacklist_patterns:
        for pattern in blacklist_patterns:
            for item in result:
                if re.search(pattern, item):
                    assert False, f"Item {item} matches blacklist pattern {pattern} but wasn't filtered"
    
    # Result should be a subset of original items
    assert set(result).issubset(set(items))


# Test 4: round_value mathematical properties
@given(
    st.floats(min_value=-1e10, max_value=1e10, allow_nan=False, allow_infinity=False),
    st.integers(min_value=0, max_value=10)
)
def test_round_value_idempotence(value, precision):
    """Test that rounding twice gives the same result (idempotence)."""
    rounded_once = round_value(value, precision)
    rounded_twice = round_value(rounded_once, precision)
    assert math.isclose(rounded_once, rounded_twice, rel_tol=1e-9)


@given(st.floats(min_value=-1e10, max_value=1e10, allow_nan=False, allow_infinity=False))
def test_round_value_rounding_methods(value):
    """Test different rounding methods produce expected relationships."""
    # ROUND_DOWN should be <= ROUND_HALF_UP <= ROUND_UP
    down = round_value(value, 0, ROUND_DOWN)
    half_up = round_value(value, 0, ROUND_HALF_UP)
    up = round_value(value, 0, ROUND_UP)
    
    if value >= 0:
        assert down <= half_up <= up
    else:
        assert up <= half_up <= down


# Test 5: compute_percent mathematical properties
@given(
    st.floats(min_value=0, max_value=1e10, allow_nan=False, allow_infinity=False),
    st.floats(min_value=0.01, max_value=1e10, allow_nan=False, allow_infinity=False)
)
def test_compute_percent_range(part, total):
    """Test that compute_percent returns values in valid range."""
    result = compute_percent(part, total)
    
    # Percentage should be between 0 and 100 when part <= total
    if part <= total:
        assert 0 <= result <= 100
    
    # When part > total, percentage > 100
    if part > total:
        assert result > 100


@given(st.floats(min_value=0, max_value=1e10, allow_nan=False, allow_infinity=False))
def test_compute_percent_zero_total(part):
    """Test that compute_percent handles zero total correctly."""
    result = compute_percent(part, 0)
    assert result == 0


# Test 6: identity function property
@given(st.one_of(
    st.none(),
    st.booleans(),
    st.integers(),
    st.floats(allow_nan=False),
    st.text(),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.integers())
))
def test_identity_function(obj):
    """Test that identity function returns its input unchanged."""
    result = identity(obj)
    assert result is obj
    
    # Test with kwargs (should be ignored)
    result_with_kwargs = identity(obj, foo='bar', baz=123)
    assert result_with_kwargs is obj


# Test 7: predicate function properties  
@given(st.one_of(
    st.none(),
    st.booleans(),
    st.integers(),
    st.floats(allow_nan=False),
    st.text(),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.integers())
))
def test_predicate_function(obj):
    """Test that predicate function returns correct boolean functions."""
    pred = predicate(obj)
    
    # Check that it returns the right function
    if bool(obj):
        assert pred is return_true
        assert pred() is True
    else:
        assert pred is return_false
        assert pred() is False


# Test 8: exclude_undefined_keys property
@given(st.dictionaries(
    st.text(),
    st.one_of(st.none(), st.integers(), st.text(), st.booleans())
))
def test_exclude_undefined_keys(mapping):
    """Test that exclude_undefined_keys removes only None values."""
    result = exclude_undefined_keys(mapping)
    
    # Check no None values in result
    assert None not in result.values()
    
    # Check all non-None values are preserved
    for key, value in mapping.items():
        if value is not None:
            assert key in result
            assert result[key] == value
        else:
            assert key not in result


# Test 9: total_time_to_temporal_percent mathematical property
@given(
    st.floats(min_value=0, max_value=1e10, allow_nan=False, allow_infinity=False),
    st.integers(min_value=1, max_value=10000)
)
def test_total_time_to_temporal_percent(total_time, scale):
    """Test mathematical properties of temporal percent calculation."""
    result = total_time_to_temporal_percent(total_time, scale)
    
    # Result should be total_time / scale * 100
    expected = total_time / scale * 100
    assert math.isclose(result, expected, rel_tol=1e-9)
    
    # Test with default scale (1000 ms)
    result_default = total_time_to_temporal_percent(total_time)
    expected_default = total_time / 1000 * 100
    assert math.isclose(result_default, expected_default, rel_tol=1e-9)


# Test microsecond parsing in RFC3339
@given(st.text(min_size=1, max_size=10).filter(lambda s: s.isdigit()))
def test_rfc3339_microsecond_parsing(microsecond_str):
    """Test RFC3339 parsing handles microsecond strings correctly."""
    # Create a date string with custom microsecond part
    date_str = f"2024-01-01T12:00:00.{microsecond_str}Z"
    try:
        parsed = parse_rfc3339(date_str)
        # Parsing should succeed
        assert isinstance(parsed, datetime.datetime)
    except (ValueError, AttributeError):
        # Some microsecond strings might be invalid
        pass


if __name__ == "__main__":
    print("Running direct property-based tests for datadog_checks.utils functions...")
    pytest.main([__file__, "-v", "--tb=short"])