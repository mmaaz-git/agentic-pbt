#!/usr/bin/env python3
"""Property-based tests for dateutil.relativedelta using Hypothesis."""

import datetime
from hypothesis import given, strategies as st, assume, settings
from dateutil.relativedelta import relativedelta
import pytest
import math


# Strategy for valid datetime values
valid_datetimes = st.datetimes(
    min_value=datetime.datetime(1900, 1, 1),
    max_value=datetime.datetime(2100, 12, 31)
)

# Strategy for valid years (avoiding overflow)
valid_years = st.integers(min_value=1900, max_value=2100)

# Strategy for months
valid_months = st.integers(min_value=1, max_value=12)

# Strategy for days (simplified, max 28 to avoid month-specific issues)
valid_days = st.integers(min_value=1, max_value=28)

# Strategy for time components
valid_hours = st.integers(min_value=0, max_value=23)
valid_minutes = st.integers(min_value=0, max_value=59)
valid_seconds = st.integers(min_value=0, max_value=59)
valid_microseconds = st.integers(min_value=0, max_value=999999)

# Strategy for relative values (keeping reasonable to avoid overflow)
relative_years = st.integers(min_value=-100, max_value=100)
relative_months = st.integers(min_value=-1200, max_value=1200)
relative_days = st.integers(min_value=-36500, max_value=36500)
relative_hours = st.integers(min_value=-876000, max_value=876000)
relative_minutes = st.integers(min_value=-525600, max_value=525600)
relative_seconds = st.integers(min_value=-31536000, max_value=31536000)
relative_microseconds = st.integers(min_value=-999999999, max_value=999999999)


@st.composite
def relativedelta_strategy(draw):
    """Generate valid relativedelta objects with various parameters."""
    # Choose what kind of relativedelta to create
    mode = draw(st.sampled_from(['relative', 'absolute', 'mixed']))
    
    if mode == 'relative':
        return relativedelta(
            years=draw(relative_years),
            months=draw(relative_months),
            days=draw(relative_days),
            hours=draw(relative_hours),
            minutes=draw(relative_minutes),
            seconds=draw(relative_seconds),
            microseconds=draw(relative_microseconds)
        )
    elif mode == 'absolute':
        return relativedelta(
            year=draw(st.one_of(st.none(), valid_years)),
            month=draw(st.one_of(st.none(), valid_months)),
            day=draw(st.one_of(st.none(), valid_days)),
            hour=draw(st.one_of(st.none(), valid_hours)),
            minute=draw(st.one_of(st.none(), valid_minutes)),
            second=draw(st.one_of(st.none(), valid_seconds)),
            microsecond=draw(st.one_of(st.none(), valid_microseconds))
        )
    else:  # mixed
        return relativedelta(
            years=draw(relative_years),
            months=draw(relative_months),
            days=draw(relative_days),
            hours=draw(relative_hours),
            minutes=draw(relative_minutes),
            seconds=draw(relative_seconds),
            microseconds=draw(relative_microseconds),
            year=draw(st.one_of(st.none(), valid_years)),
            month=draw(st.one_of(st.none(), valid_months)),
            day=draw(st.one_of(st.none(), valid_days)),
            hour=draw(st.one_of(st.none(), valid_hours)),
            minute=draw(st.one_of(st.none(), valid_minutes)),
            second=draw(st.one_of(st.none(), valid_seconds)),
            microsecond=draw(st.one_of(st.none(), valid_microseconds))
        )


# Test 1: Round-trip property - creating relativedelta from two dates
@given(valid_datetimes, valid_datetimes)
@settings(max_examples=500)
def test_relativedelta_round_trip(dt1, dt2):
    """Test that creating a relativedelta from two dates and applying it gives correct result."""
    # Create relativedelta from the difference
    rd = relativedelta(dt1, dt2)
    
    # Apply it back
    result = dt2 + rd
    
    # Should get back to dt1
    assert result == dt1, f"Round trip failed: {dt2} + {rd} = {result}, expected {dt1}"


# Test 2: Inverse operations - adding and subtracting
@given(valid_datetimes, relativedelta_strategy())
@settings(max_examples=500)
def test_relativedelta_inverse_operations(dt, rd):
    """Test that adding and then subtracting a relativedelta gives back the original date."""
    # Skip if the operation would overflow
    try:
        dt_plus_rd = dt + rd
        dt_round_trip = dt_plus_rd + (-rd)
    except (ValueError, OverflowError):
        assume(False)
    
    # Due to month boundary issues, this might not always be exact
    # But the difference should be small
    if dt != dt_round_trip:
        # Check if it's a month boundary issue
        diff = abs((dt - dt_round_trip).total_seconds())
        # Allow up to 3 days difference for month boundary cases
        assert diff <= 3 * 24 * 3600, f"Inverse operation failed by too much: {dt} != {dt_round_trip}, diff={diff}s"


# Test 3: Normalization idempotence
@given(relativedelta_strategy())
@settings(max_examples=500)
def test_normalized_idempotence(rd):
    """Test that normalizing twice gives the same result."""
    normalized_once = rd.normalized()
    normalized_twice = normalized_once.normalized()
    
    assert normalized_once == normalized_twice, f"Normalization not idempotent: {normalized_once} != {normalized_twice}"


# Test 4: Negation properties
@given(relativedelta_strategy())
@settings(max_examples=500)
def test_negation_properties(rd):
    """Test that negation works correctly."""
    neg_rd = -rd
    double_neg = -neg_rd
    
    # Check relative fields are negated
    assert neg_rd.years == -rd.years
    assert neg_rd.months == -rd.months
    assert neg_rd.days == -rd.days
    assert neg_rd.hours == -rd.hours
    assert neg_rd.minutes == -rd.minutes
    assert neg_rd.seconds == -rd.seconds
    assert neg_rd.microseconds == -rd.microseconds
    
    # Absolute fields should remain unchanged
    assert neg_rd.year == rd.year
    assert neg_rd.month == rd.month
    assert neg_rd.day == rd.day
    assert neg_rd.hour == rd.hour
    assert neg_rd.minute == rd.minute
    assert neg_rd.second == rd.second
    assert neg_rd.microsecond == rd.microsecond
    
    # Double negation should give back original (for relative parts)
    assert double_neg.years == rd.years
    assert double_neg.months == rd.months
    assert double_neg.days == rd.days


# Test 5: Multiplication by scalar
@given(relativedelta_strategy(), st.floats(min_value=-100, max_value=100, allow_nan=False, allow_infinity=False))
@settings(max_examples=500)
def test_multiplication_scalar(rd, scalar):
    """Test multiplication by scalar."""
    try:
        result = rd * scalar
    except (ValueError, OverflowError):
        assume(False)
    
    # Check that relative fields are multiplied
    expected_years = int(rd.years * scalar)
    expected_months = int(rd.months * scalar)
    expected_days = int(rd.days * scalar)
    
    assert result.years == expected_years
    assert result.months == expected_months
    assert result.days == expected_days
    
    # Absolute fields should remain unchanged
    assert result.year == rd.year
    assert result.month == rd.month
    assert result.day == rd.day


# Test 6: Addition of relativedeltas is associative
@given(relativedelta_strategy(), relativedelta_strategy(), relativedelta_strategy())
@settings(max_examples=500)
def test_addition_associative(rd1, rd2, rd3):
    """Test that (rd1 + rd2) + rd3 == rd1 + (rd2 + rd3)."""
    left_assoc = (rd1 + rd2) + rd3
    right_assoc = rd1 + (rd2 + rd3)
    
    # Check all relative fields
    assert left_assoc.years == right_assoc.years
    assert left_assoc.months == right_assoc.months
    assert left_assoc.days == right_assoc.days
    assert left_assoc.hours == right_assoc.hours
    assert left_assoc.minutes == right_assoc.minutes
    assert left_assoc.seconds == right_assoc.seconds
    assert left_assoc.microseconds == right_assoc.microseconds


# Test 7: Boolean evaluation consistency
@given(relativedelta_strategy())
@settings(max_examples=500)
def test_bool_consistency(rd):
    """Test that bool evaluation is consistent."""
    is_truthy = bool(rd)
    
    # A relativedelta should be falsy only if all fields are zero/None
    all_relative_zero = (
        rd.years == 0 and rd.months == 0 and rd.days == 0 and
        rd.hours == 0 and rd.minutes == 0 and rd.seconds == 0 and
        rd.microseconds == 0 and rd.leapdays == 0
    )
    all_absolute_none = (
        rd.year is None and rd.month is None and rd.day is None and
        rd.weekday is None and rd.hour is None and rd.minute is None and
        rd.second is None and rd.microsecond is None
    )
    
    should_be_falsy = all_relative_zero and all_absolute_none
    
    assert is_truthy != should_be_falsy, f"Bool evaluation inconsistent for {rd}"


# Test 8: Hash consistency with equality
@given(relativedelta_strategy(), relativedelta_strategy())
@settings(max_examples=500)
def test_hash_consistency(rd1, rd2):
    """Test that equal objects have equal hashes."""
    if rd1 == rd2:
        assert hash(rd1) == hash(rd2), f"Equal objects have different hashes: {rd1} and {rd2}"


# Test 9: Weeks property consistency
@given(relative_days)
@settings(max_examples=500)
def test_weeks_property(days):
    """Test that weeks property correctly represents days."""
    rd = relativedelta(days=days)
    
    # Weeks should be the integer division of days by 7
    expected_weeks = int(days / 7.0)
    assert rd.weeks == expected_weeks
    
    # Setting weeks should update days correctly
    rd.weeks = 10
    # Days should be updated to remove old weeks and add new ones
    expected_days = days - (expected_weeks * 7) + (10 * 7)
    assert rd.days == expected_days


# Test 10: Edge case - empty relativedelta
@given(valid_datetimes)
@settings(max_examples=100)
def test_empty_relativedelta(dt):
    """Test that an empty relativedelta doesn't change a date."""
    rd = relativedelta()
    result = dt + rd
    assert result == dt, f"Empty relativedelta changed date: {dt} -> {result}"


# Test 11: Yearday and nlyearday handling
@given(st.integers(min_value=1, max_value=366))
@settings(max_examples=500)
def test_yearday_handling(yday):
    """Test yearday parameter handling."""
    if yday > 366:
        with pytest.raises(ValueError):
            rd = relativedelta(yearday=yday)
    else:
        try:
            rd = relativedelta(yearday=yday)
            # Should set month and day appropriately
            assert rd.month is not None
            assert rd.day is not None
            # Verify it's a valid date
            assert 1 <= rd.month <= 12
            assert 1 <= rd.day <= 31
        except ValueError as e:
            # Should only fail for invalid yearday
            assert yday > 366 or yday < 1, f"Unexpected ValueError for yearday={yday}: {e}"


# Test 12: Division by scalar (inverse of multiplication)
@given(relativedelta_strategy(), st.floats(min_value=0.1, max_value=100, allow_nan=False, allow_infinity=False))
@settings(max_examples=500)
def test_division_scalar(rd, divisor):
    """Test division by scalar."""
    try:
        result = rd / divisor
    except (ValueError, OverflowError, ZeroDivisionError):
        assume(False)
    
    # Should be equivalent to multiplication by reciprocal
    reciprocal = 1 / divisor
    mult_result = rd * reciprocal
    
    # Check that results are the same
    assert result.years == mult_result.years
    assert result.months == mult_result.months
    assert result.days == mult_result.days


if __name__ == "__main__":
    print("Running property-based tests for dateutil.relativedelta...")
    pytest.main([__file__, "-v", "--tb=short"])