#!/usr/bin/env python3
import math
from datetime import datetime, time, timedelta, timezone
from hypothesis import given, strategies as st, assume, settings
import dateutil.utils
from dateutil import tz


# Strategy for generating datetime objects
datetime_strategy = st.datetimes(
    min_value=datetime(1900, 1, 1),
    max_value=datetime(2200, 12, 31),
    timezones=st.none() | st.timezones()
)

# Strategy for timedelta
timedelta_strategy = st.timedeltas(
    min_value=timedelta(microseconds=-10**15),
    max_value=timedelta(microseconds=10**15)
)

# Strategy for tzinfo objects
tzinfo_strategy = st.one_of(
    st.none(),
    st.timezones(),
    st.builds(tz.tzutc),
    st.builds(tz.tzoffset, st.text(min_size=1, max_size=10), st.integers(min_value=-86400, max_value=86400))
)


# Test 1: within_delta symmetry property
@given(datetime_strategy, datetime_strategy, timedelta_strategy)
def test_within_delta_symmetry(dt1, dt2, delta):
    """within_delta(a, b, d) should equal within_delta(b, a, d)"""
    result1 = dateutil.utils.within_delta(dt1, dt2, delta)
    result2 = dateutil.utils.within_delta(dt2, dt1, delta)
    assert result1 == result2, f"Symmetry violated: within_delta({dt1}, {dt2}, {delta}) != within_delta({dt2}, {dt1}, {delta})"


# Test 2: within_delta reflexivity
@given(datetime_strategy, timedelta_strategy)
def test_within_delta_reflexivity(dt, delta):
    """within_delta(a, a, d) should always be True for any non-negative delta"""
    result = dateutil.utils.within_delta(dt, dt, delta)
    assert result == True, f"Reflexivity violated: within_delta({dt}, {dt}, {delta}) returned False"


# Test 3: within_delta with negative delta
@given(datetime_strategy, datetime_strategy, timedelta_strategy)
def test_within_delta_handles_negative_delta(dt1, dt2, delta):
    """within_delta should handle negative deltas by using abs(delta)"""
    result_pos = dateutil.utils.within_delta(dt1, dt2, delta)
    result_neg = dateutil.utils.within_delta(dt1, dt2, -delta)
    assert result_pos == result_neg, f"Negative delta handling broken: different results for delta={delta} and delta={-delta}"


# Test 4: default_tzinfo idempotence
@given(datetime_strategy, tzinfo_strategy)
def test_default_tzinfo_idempotence(dt, tzinfo):
    """Applying default_tzinfo twice should equal applying it once"""
    once = dateutil.utils.default_tzinfo(dt, tzinfo)
    twice = dateutil.utils.default_tzinfo(once, tzinfo)
    assert once == twice, f"Idempotence violated: applying default_tzinfo twice changed the result"


# Test 5: default_tzinfo preserves aware datetimes
@given(st.datetimes(timezones=st.timezones()), tzinfo_strategy)
def test_default_tzinfo_preserves_aware(aware_dt, tzinfo):
    """default_tzinfo should not modify aware datetimes"""
    result = dateutil.utils.default_tzinfo(aware_dt, tzinfo)
    assert result == aware_dt, f"Aware datetime was modified: {aware_dt} -> {result}"
    assert result.tzinfo == aware_dt.tzinfo, f"tzinfo was changed on aware datetime"


# Test 6: default_tzinfo sets tzinfo on naive datetimes
@given(st.datetimes(timezones=st.none()), tzinfo_strategy)
def test_default_tzinfo_sets_naive(naive_dt, tzinfo):
    """default_tzinfo should set tzinfo on naive datetimes"""
    result = dateutil.utils.default_tzinfo(naive_dt, tzinfo)
    assert result.tzinfo == tzinfo, f"tzinfo not set correctly: expected {tzinfo}, got {result.tzinfo}"
    # Check that other components are preserved
    assert result.replace(tzinfo=None) == naive_dt, f"Date/time components were modified"


# Test 7: today() returns midnight
@given(tzinfo_strategy)
@settings(max_examples=50)  # Reduce examples since this involves current time
def test_today_returns_midnight(tzinfo):
    """today() should always return a datetime at midnight (00:00:00.000000)"""
    result = dateutil.utils.today(tzinfo)
    assert result.hour == 0, f"Hour is not 0: {result.hour}"
    assert result.minute == 0, f"Minute is not 0: {result.minute}"
    assert result.second == 0, f"Second is not 0: {result.second}"
    assert result.microsecond == 0, f"Microsecond is not 0: {result.microsecond}"


# Test 8: today() has correct timezone
@given(tzinfo_strategy)
@settings(max_examples=50)
def test_today_timezone_consistency(tzinfo):
    """today() should have the same tzinfo as provided"""
    result = dateutil.utils.today(tzinfo)
    if tzinfo is None:
        assert result.tzinfo is None, f"Expected naive datetime, got tzinfo={result.tzinfo}"
    else:
        assert result.tzinfo == tzinfo, f"tzinfo mismatch: expected {tzinfo}, got {result.tzinfo}"


# Test 9: within_delta triangle inequality-like property
@given(datetime_strategy, datetime_strategy, datetime_strategy, timedelta_strategy)
def test_within_delta_triangle_property(dt1, dt2, dt3, delta):
    """If dt1 and dt2 are within delta, and dt2 and dt3 are within delta,
    then dt1 and dt3 should be within 2*delta"""
    if dateutil.utils.within_delta(dt1, dt2, delta) and dateutil.utils.within_delta(dt2, dt3, delta):
        # dt1 and dt3 should be within 2*delta
        double_delta = delta * 2
        result = dateutil.utils.within_delta(dt1, dt3, double_delta)
        assert result, f"Triangle property violated: dt1={dt1}, dt2={dt2}, dt3={dt3}, delta={delta}"


# Test 10: within_delta boundary conditions
@given(datetime_strategy, timedelta_strategy)
def test_within_delta_exact_boundary(dt, delta):
    """Test exact boundary: dt and dt+delta should be within delta of each other"""
    dt2 = dt + delta
    result = dateutil.utils.within_delta(dt, dt2, delta)
    assert result == True, f"Boundary condition failed: {dt} and {dt2} should be within {delta}"


# Test 11: Check if today() actually returns today's date
@given(tzinfo_strategy)
@settings(max_examples=20)
def test_today_returns_current_date(tzinfo):
    """today() should return the current date"""
    result = dateutil.utils.today(tzinfo)
    now = datetime.now(tzinfo)
    # They should have the same date (accounting for possible timezone differences at boundaries)
    # Allow for 1 day difference in case we're at a day boundary during execution
    date_diff = abs((result.date() - now.date()).days)
    assert date_diff <= 1, f"Date mismatch: today() returned {result.date()}, but now is {now.date()}"


if __name__ == "__main__":
    import pytest
    import sys
    sys.exit(pytest.main([__file__, "-v"]))