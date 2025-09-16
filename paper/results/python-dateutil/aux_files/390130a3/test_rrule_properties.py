import datetime
import math
from hypothesis import given, strategies as st, assume, settings, example
from dateutil import rrule
import pytest


# Strategies for valid rrule inputs
freq_strategy = st.sampled_from([
    rrule.YEARLY, rrule.MONTHLY, rrule.WEEKLY, rrule.DAILY,
    rrule.HOURLY, rrule.MINUTELY, rrule.SECONDLY
])

# Safe datetime strategy - avoiding edge cases initially
safe_datetime = st.datetimes(
    min_value=datetime.datetime(1900, 1, 1),
    max_value=datetime.datetime(2100, 1, 1)
).map(lambda dt: dt.replace(microsecond=0))  # rrule ignores microseconds

# Interval strategy - reasonable values
interval_strategy = st.integers(min_value=1, max_value=100)

# Count strategy - reasonable counts
count_strategy = st.integers(min_value=1, max_value=100)

# Bymonth strategy
bymonth_strategy = st.one_of(
    st.none(),
    st.integers(min_value=1, max_value=12),
    st.lists(st.integers(min_value=1, max_value=12), min_size=1, max_size=12).map(tuple)
)

# Bymonthday strategy  
bymonthday_strategy = st.one_of(
    st.none(),
    st.integers(min_value=-31, max_value=31).filter(lambda x: x != 0),
    st.lists(st.integers(min_value=-31, max_value=31).filter(lambda x: x != 0), 
             min_size=1, max_size=10).map(tuple)
)

# Byweekday strategy
byweekday_strategy = st.one_of(
    st.none(),
    st.sampled_from([rrule.MO, rrule.TU, rrule.WE, rrule.TH, rrule.FR, rrule.SA, rrule.SU]),
    st.lists(st.sampled_from([rrule.MO, rrule.TU, rrule.WE, rrule.TH, rrule.FR, rrule.SA, rrule.SU]),
             min_size=1, max_size=7).map(tuple)
)


@given(
    freq=freq_strategy,
    dtstart=safe_datetime,
    interval=interval_strategy,
    count=count_strategy
)
def test_count_property(freq, dtstart, interval, count):
    """Test that count parameter produces exactly that many events"""
    rule = rrule.rrule(freq, dtstart=dtstart, interval=interval, count=count)
    events = list(rule)
    assert len(events) == count, f"Expected {count} events but got {len(events)}"


@given(
    freq=freq_strategy,
    dtstart=safe_datetime,
    interval=interval_strategy,
    count=count_strategy
)
def test_ordering_property(freq, dtstart, interval, count):
    """Test that generated dates are always in chronological order"""
    rule = rrule.rrule(freq, dtstart=dtstart, interval=interval, count=count)
    events = list(rule)
    
    for i in range(1, len(events)):
        assert events[i] > events[i-1], f"Events not in order: {events[i-1]} >= {events[i]}"


@given(
    freq=freq_strategy,
    dtstart=safe_datetime,
    interval=interval_strategy,
    days_until=st.integers(min_value=1, max_value=365)
)
def test_until_boundary(freq, dtstart, interval, days_until):
    """Test that until parameter is inclusive"""
    until = dtstart + datetime.timedelta(days=days_until)
    rule = rrule.rrule(freq, dtstart=dtstart, interval=interval, until=until)
    events = list(rule)
    
    if events:
        # All events should be <= until
        for event in events:
            assert event <= until, f"Event {event} exceeds until {until}"


@given(
    freq=freq_strategy,
    dtstart=safe_datetime,
    interval=interval_strategy,
    count=st.integers(min_value=10, max_value=50)
)
def test_before_after_partition(freq, dtstart, interval, count):
    """Test that before() and after() partition the events correctly"""
    rule = rrule.rrule(freq, dtstart=dtstart, interval=interval, count=count)
    all_events = list(rule)
    
    if len(all_events) >= 3:
        # Pick a middle event as pivot
        pivot_idx = len(all_events) // 2
        pivot = all_events[pivot_idx]
        
        # Get events before and after (exclusive)
        before_event = rule.before(pivot, inc=False)
        after_event = rule.after(pivot, inc=False)
        
        # Check correctness
        if before_event:
            assert before_event < pivot
            assert before_event in all_events
            
        if after_event:
            assert after_event > pivot
            assert after_event in all_events


@given(
    freq=freq_strategy,
    dtstart=safe_datetime,
    interval=interval_strategy,
    count=st.integers(min_value=20, max_value=50)
)
def test_between_completeness(freq, dtstart, interval, count):
    """Test that between() returns all events in the range"""
    rule = rrule.rrule(freq, dtstart=dtstart, interval=interval, count=count)
    all_events = list(rule)
    
    if len(all_events) >= 5:
        # Pick a range
        start_idx = len(all_events) // 4
        end_idx = 3 * len(all_events) // 4
        
        after = all_events[start_idx]
        before = all_events[end_idx]
        
        # Get events between (exclusive)
        between_events = rule.between(after, before, inc=False)
        
        # Check that we got all events in range
        expected = [e for e in all_events if after < e < before]
        assert between_events == expected


@given(
    freq=freq_strategy,
    dtstart=safe_datetime,
    interval=interval_strategy,
    count=count_strategy
)
def test_cache_consistency(freq, dtstart, interval, count):
    """Test that cached and non-cached versions produce identical results"""
    rule_cached = rrule.rrule(freq, dtstart=dtstart, interval=interval, count=count, cache=True)
    rule_uncached = rrule.rrule(freq, dtstart=dtstart, interval=interval, count=count, cache=False)
    
    # Iterate multiple times to test caching
    events_cached_1 = list(rule_cached)
    events_cached_2 = list(rule_cached)
    events_uncached = list(rule_uncached)
    
    assert events_cached_1 == events_cached_2 == events_uncached


@given(
    freq=freq_strategy,
    dtstart=safe_datetime,
    interval=interval_strategy,
    count=count_strategy
)
def test_contains_property(freq, dtstart, interval, count):
    """Test that __contains__ works correctly"""
    rule = rrule.rrule(freq, dtstart=dtstart, interval=interval, count=count)
    events = list(rule)
    
    # All generated events should be contained
    for event in events:
        assert event in rule
    
    # Events not in the list should not be contained
    if events:
        # Test with a datetime definitely not in the rule
        fake_event = events[0] + datetime.timedelta(microseconds=1)
        if fake_event not in events:
            assert fake_event not in rule


@given(
    freq=freq_strategy,
    dtstart=safe_datetime,
    interval=interval_strategy,
    count=st.integers(min_value=5, max_value=20)
)
def test_getitem_consistency(freq, dtstart, interval, count):
    """Test that indexing works correctly"""
    rule = rrule.rrule(freq, dtstart=dtstart, interval=interval, count=count)
    events = list(rule)
    
    # Test positive indexing
    for i in range(len(events)):
        assert rule[i] == events[i]
    
    # Test negative indexing
    if events:
        assert rule[-1] == events[-1]
        if len(events) > 1:
            assert rule[-2] == events[-2]


@given(
    freq=freq_strategy,
    dtstart=safe_datetime,
    interval=interval_strategy,
    count=st.integers(min_value=10, max_value=30)
)
def test_slice_consistency(freq, dtstart, interval, count):
    """Test that slicing works correctly"""
    rule = rrule.rrule(freq, dtstart=dtstart, interval=interval, count=count)
    events = list(rule)
    
    # Test various slices
    assert rule[1:5] == events[1:5]
    assert rule[::2] == events[::2]
    assert rule[:5] == events[:5]
    assert rule[5:] == events[5:]


@given(
    freq=freq_strategy,
    dtstart=safe_datetime,
    interval=interval_strategy,
    bymonth=bymonth_strategy,
    bymonthday=bymonthday_strategy
)
def test_bymonth_bymonthday_validation(freq, dtstart, interval, bymonth, bymonthday):
    """Test that bymonth and bymonthday constraints are respected"""
    assume(bymonth is not None or bymonthday is not None)
    
    # Limit count to avoid very long computations
    rule = rrule.rrule(freq, dtstart=dtstart, interval=interval, 
                       count=min(50, 365 if freq >= rrule.DAILY else 100),
                       bymonth=bymonth, bymonthday=bymonthday)
    events = list(rule)
    
    if bymonth is not None:
        months = [bymonth] if isinstance(bymonth, int) else bymonth
        for event in events:
            assert event.month in months
    
    if bymonthday is not None:
        monthdays = [bymonthday] if isinstance(bymonthday, int) else bymonthday
        for event in events:
            day = event.day
            if any(md < 0 for md in monthdays):
                # Handle negative monthdays
                import calendar
                last_day = calendar.monthrange(event.year, event.month)[1]
                valid_days = set()
                for md in monthdays:
                    if md > 0:
                        valid_days.add(md)
                    else:
                        valid_days.add(last_day + md + 1)
                assert day in valid_days
            else:
                assert day in monthdays


@given(
    freq=st.sampled_from([rrule.WEEKLY]),
    dtstart=safe_datetime,
    interval=interval_strategy,
    byweekday=byweekday_strategy,
    count=st.integers(min_value=1, max_value=20)
)
def test_byweekday_validation(freq, dtstart, interval, byweekday, count):
    """Test that byweekday constraints are respected"""
    assume(byweekday is not None)
    
    rule = rrule.rrule(freq, dtstart=dtstart, interval=interval, 
                       byweekday=byweekday, count=count)
    events = list(rule)
    
    if byweekday is not None:
        if hasattr(byweekday, 'weekday'):
            weekdays = [byweekday.weekday]
        elif isinstance(byweekday, tuple):
            weekdays = [wd.weekday if hasattr(wd, 'weekday') else wd for wd in byweekday]
        else:
            weekdays = [byweekday]
        
        for event in events:
            assert event.weekday() in weekdays


@given(
    freq=freq_strategy,
    dtstart=safe_datetime,
    interval=interval_strategy,
    count=st.integers(min_value=5, max_value=20)
)
def test_xafter_generator(freq, dtstart, interval, count):
    """Test xafter generator method"""
    rule = rrule.rrule(freq, dtstart=dtstart, interval=interval, count=count)
    all_events = list(rule)
    
    if len(all_events) >= 3:
        pivot = all_events[1]  # Start after first event
        
        # Get next 3 events after pivot (exclusive)
        xafter_events = list(rule.xafter(pivot, count=3, inc=False))
        
        # Should match the corresponding slice from all_events
        expected = [e for e in all_events if e > pivot][:3]
        assert xafter_events == expected


@given(
    freq=freq_strategy,
    dtstart=safe_datetime,
    interval=interval_strategy,
    count=count_strategy
)
def test_count_method(freq, dtstart, interval, count):
    """Test the count() method returns correct value"""
    rule = rrule.rrule(freq, dtstart=dtstart, interval=interval, count=count)
    
    # The count() method should return the number of occurrences
    assert rule.count() == count
    
    # After calling count(), it should be cached
    assert rule.count() == count  # Second call should return same


@given(
    freq=freq_strategy, 
    dtstart=safe_datetime,
    new_interval=interval_strategy,
    new_count=count_strategy
)
def test_replace_method(freq, dtstart, new_interval, new_count):
    """Test that replace() creates a new rule with updated parameters"""
    original = rrule.rrule(freq, dtstart=dtstart, interval=1, count=10)
    
    # Replace with new values
    replaced = original.replace(interval=new_interval, count=new_count)
    
    # Check that new rule has updated values
    assert replaced._interval == new_interval
    assert replaced._count == new_count
    assert replaced._freq == freq
    assert replaced._dtstart == dtstart
    
    # Original should be unchanged
    assert original._interval == 1
    assert original._count == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])