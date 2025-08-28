#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/limits_env/lib/python3.13/site-packages')

from hypothesis import given, assume, strategies as st, settings
import limits
from limits.limits import RateLimitItem, RateLimitItemPerSecond, RateLimitItemPerMinute
from limits.limits import RateLimitItemPerHour, RateLimitItemPerDay, RateLimitItemPerMonth, RateLimitItemPerYear
from limits.limits import safe_string, TIME_TYPES
from limits.util import parse, parse_many


@given(st.one_of(
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.text(),
    st.binary()
))
def test_safe_string_handles_all_types(value):
    result = safe_string(value)
    assert isinstance(result, str)
    if isinstance(value, bytes):
        assert result == value.decode()
    else:
        assert result == str(value)


rate_limit_classes = [
    RateLimitItemPerSecond,
    RateLimitItemPerMinute, 
    RateLimitItemPerHour,
    RateLimitItemPerDay,
    RateLimitItemPerMonth,
    RateLimitItemPerYear
]

@given(
    st.sampled_from(rate_limit_classes),
    st.integers(min_value=1, max_value=1000),
    st.integers(min_value=1, max_value=100),
    st.text(min_size=1, max_size=20).filter(lambda x: '/' not in x)
)
def test_rate_limit_key_for_deterministic(cls, amount, multiples, namespace):
    limit = cls(amount, multiples, namespace)
    
    key1 = limit.key_for()
    key2 = limit.key_for()
    assert key1 == key2
    
    identifiers = ["user123", 456, 78.9, b"bytes"]
    key3 = limit.key_for(*identifiers)
    key4 = limit.key_for(*identifiers)
    assert key3 == key4
    
    assert namespace in key1
    assert str(amount) in key1
    assert str(multiples) in key1
    assert cls.GRANULARITY.name in key1


@given(
    st.sampled_from(rate_limit_classes),
    st.integers(min_value=1, max_value=1000),
    st.integers(min_value=1, max_value=100)
)
def test_get_expiry_returns_correct_seconds(cls, amount, multiples):
    limit = cls(amount, multiples)
    expiry = limit.get_expiry()
    
    assert expiry == cls.GRANULARITY.seconds * multiples
    assert expiry > 0
    assert isinstance(expiry, int)


@given(
    st.sampled_from(rate_limit_classes),
    st.integers(min_value=1, max_value=1000),
    st.integers(min_value=1, max_value=100)
)
def test_rate_limit_equality_and_hash(cls, amount, multiples):
    limit1 = cls(amount, multiples, "NS1")
    limit2 = cls(amount, multiples, "NS1")
    limit3 = cls(amount, multiples, "NS2")
    
    assert limit1 == limit2
    assert hash(limit1) == hash(limit2)
    
    assert limit1 != limit3
    assert hash(limit1) != hash(limit3)


@given(
    st.integers(min_value=1, max_value=999),
    st.sampled_from(["second", "minute", "hour", "day", "month", "year"])
)
def test_parse_single_rate_limit(amount, granularity):
    limit_string = f"{amount}/{granularity}"
    limit = parse(limit_string)
    
    assert limit.amount == amount
    assert limit.multiples == 1
    assert limit.GRANULARITY.name == granularity


@given(
    st.integers(min_value=1, max_value=999),
    st.integers(min_value=1, max_value=100),
    st.sampled_from(["second", "minute", "hour", "day", "month", "year"])
)
def test_parse_rate_limit_with_multiples(amount, multiples, granularity):
    limit_string = f"{amount}/{multiples} {granularity}"
    limit = parse(limit_string)
    
    assert limit.amount == amount
    assert limit.multiples == multiples
    assert limit.GRANULARITY.name == granularity


@given(
    st.integers(min_value=1, max_value=999),
    st.sampled_from(["second", "minute", "hour", "day", "month", "year"])
)
def test_parse_with_per_syntax(amount, granularity):
    limit_string = f"{amount} per {granularity}"
    limit = parse(limit_string)
    
    assert limit.amount == amount
    assert limit.multiples == 1
    assert limit.GRANULARITY.name == granularity


@given(
    st.lists(
        st.tuples(
            st.integers(min_value=1, max_value=999),
            st.sampled_from(["second", "minute", "hour", "day", "month", "year"])
        ),
        min_size=1,
        max_size=5
    ),
    st.sampled_from([",", ";", "|"])
)
def test_parse_many_with_separators(limits_data, separator):
    limit_strings = [f"{amount}/{granularity}" for amount, granularity in limits_data]
    combined_string = separator.join(limit_strings)
    
    parsed_limits = parse_many(combined_string)
    
    assert len(parsed_limits) == len(limits_data)
    for parsed, (amount, granularity) in zip(parsed_limits, limits_data):
        assert parsed.amount == amount
        assert parsed.GRANULARITY.name == granularity


@given(
    st.sampled_from(rate_limit_classes),
    st.integers(min_value=1, max_value=999),
    st.integers(min_value=1, max_value=100)
)
def test_repr_parse_round_trip(cls, amount, multiples):
    original_limit = cls(amount, multiples)
    repr_string = repr(original_limit)
    
    parsed_limit = parse(repr_string)
    
    assert parsed_limit.amount == original_limit.amount
    assert parsed_limit.multiples == original_limit.multiples
    assert parsed_limit.GRANULARITY == original_limit.GRANULARITY


@given(
    st.lists(
        st.sampled_from(rate_limit_classes),
        min_size=2,
        max_size=5
    )
)
def test_rate_limit_ordering(classes):
    limits = [cls(10, 1) for cls in classes]
    
    sorted_limits = sorted(limits)
    
    for i in range(len(sorted_limits) - 1):
        assert sorted_limits[i].GRANULARITY.seconds <= sorted_limits[i+1].GRANULARITY.seconds


@given(st.text())
def test_parse_invalid_strings_raise_error(invalid_string):
    assume(not any(c.isdigit() for c in invalid_string))
    
    try:
        parse(invalid_string)
        assert False, f"Should have raised ValueError for '{invalid_string}'"
    except ValueError as e:
        assert "couldn't parse rate limit string" in str(e)


@given(
    st.integers(min_value=1, max_value=999),
    st.sampled_from(["seconds", "minutes", "hours", "days", "months", "years"])
)
def test_parse_plural_granularities(amount, granularity_plural):
    limit_string = f"{amount}/{granularity_plural}"
    limit = parse(limit_string)
    
    granularity_singular = granularity_plural.rstrip('s')
    assert limit.amount == amount
    assert limit.GRANULARITY.name == granularity_singular


@given(
    st.sampled_from(rate_limit_classes),
    st.integers(min_value=1, max_value=999),
    st.one_of(st.none(), st.integers(min_value=1, max_value=100))
)
def test_multiples_default_behavior(cls, amount, multiples):
    if multiples is None:
        limit = cls(amount, multiples)
        assert limit.multiples == 1
    else:
        limit = cls(amount, multiples)
        assert limit.multiples == multiples


@given(
    st.sampled_from(rate_limit_classes),
    st.floats(min_value=1.0, max_value=999.9),
    st.floats(min_value=1.0, max_value=99.9)
)
def test_rate_limit_accepts_floats_as_ints(cls, amount_float, multiples_float):
    limit = cls(amount_float, multiples_float)
    
    assert limit.amount == int(amount_float)
    assert limit.multiples == int(multiples_float)
    assert isinstance(limit.amount, int)
    assert isinstance(limit.multiples, int)


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])