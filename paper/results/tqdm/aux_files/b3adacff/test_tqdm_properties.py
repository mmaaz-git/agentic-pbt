"""Property-based tests for tqdm.auto"""

import sys
from io import StringIO
from hypothesis import given, strategies as st, assume, settings
from tqdm.auto import tqdm, trange
import math


@given(st.integers(min_value=0, max_value=10000),
       st.lists(st.integers(min_value=-100, max_value=100), min_size=1, max_size=100))
def test_update_accumulates(total, updates):
    """Property: Calling update(n) multiple times should accumulate position correctly"""
    old_stderr = sys.stderr
    sys.stderr = StringIO()
    try:
        t = tqdm(total=total)
        expected_n = 0
    
        for update_val in updates:
            t.update(update_val)
            expected_n += update_val
            # Allow n to be clamped at 0 (no negative progress)
            expected_n = max(0, expected_n)
            assert t.n == expected_n, f"After updates, expected n={expected_n}, got n={t.n}"
    
        t.close()
    finally:
        sys.stderr = old_stderr


@given(st.integers(min_value=0, max_value=10000),
       st.integers(min_value=0, max_value=10000))
def test_reset_sets_n_to_zero(initial_total, update_amount):
    """Property: reset() should always set n back to 0"""
    old_stderr = sys.stderr
    sys.stderr = StringIO()
    try:
        t = tqdm(total=initial_total)
    
        # Update to some position
        t.update(update_amount)
    
        # Reset should bring n back to 0
        t.reset()
        assert t.n == 0, f"After reset(), n should be 0 but got {t.n}"
    
        t.close()
    finally:
        sys.stderr = old_stderr


@given(st.integers(min_value=0, max_value=10000),
       st.integers(min_value=0, max_value=10000),
       st.integers(min_value=0, max_value=10000))
def test_reset_with_total_changes_total(initial_total, update_amount, new_total):
    """Property: reset(total=x) should set total to x and n to 0"""
    old_stderr = sys.stderr
    sys.stderr = StringIO()
    try:
        t = tqdm(total=initial_total)
    
        # Update to some position
        t.update(update_amount)
    
        # Reset with new total
        t.reset(total=new_total)
        assert t.n == 0, f"After reset(total={new_total}), n should be 0 but got {t.n}"
        assert t.total == new_total, f"After reset(total={new_total}), total should be {new_total} but got {t.total}"
    
        t.close()
    finally:
        sys.stderr = old_stderr


@given(st.one_of(
    st.integers(min_value=0, max_value=100),
    st.tuples(st.integers(min_value=0, max_value=100), 
              st.integers(min_value=0, max_value=100)).map(lambda x: (x[0], x[0] + x[1])),
    st.tuples(st.integers(min_value=0, max_value=100),
              st.integers(min_value=0, max_value=100),
              st.integers(min_value=1, max_value=10)).map(lambda x: (x[0], x[0] + x[1], x[2]))
))
def test_trange_equals_range(args):
    """Property: trange(*args) should produce same values as range(*args)"""
    if isinstance(args, int):
        args = (args,)
    
    # Get results
    trange_result = list(trange(*args, disable=True))
    range_result = list(range(*args))
    
    assert trange_result == range_result, f"trange{args} != range{args}: {trange_result} != {range_result}"


@given(st.lists(st.one_of(st.integers(), st.floats(allow_nan=False, allow_infinity=False), st.text()), 
                min_size=0, max_size=100))
def test_iteration_preserves_items(items):
    """Property: Iterating through tqdm should yield all original items in order"""
    old_stderr = sys.stderr
    sys.stderr = StringIO()
    try:
        collected = []
        for item in tqdm(items):
            collected.append(item)
    
        assert collected == items, f"Items not preserved: expected {items}, got {collected}"
    finally:
        sys.stderr = old_stderr


@given(st.floats(min_value=0, max_value=1e10, allow_nan=False, allow_infinity=False))
def test_format_interval_inverse(seconds):
    """Property: format_interval should handle non-negative times correctly"""
    result = tqdm.format_interval(seconds)
    assert isinstance(result, str), f"format_interval should return string, got {type(result)}"
    
    # Basic format validation
    if seconds < 60:
        # Should be MM:SS format
        assert ':' in result and result.count(':') == 1
    elif seconds < 3600:
        # Should be MM:SS format
        assert ':' in result and result.count(':') == 1
    else:
        # Should be H:MM:SS or HH:MM:SS format
        assert result.count(':') == 2


@given(st.integers())
def test_format_num_preserves_value(n):
    """Property: format_num should preserve the numeric value (just format it)"""
    result = tqdm.format_num(n)
    assert isinstance(result, str), f"format_num should return string, got {type(result)}"
    
    # For non-negative numbers, the string should represent the same number
    if n >= 0:
        # Remove any formatting characters (like commas) and check if it's the same number
        cleaned = result.replace(',', '').replace(' ', '')
        assert cleaned == str(n), f"format_num({n}) = '{result}' doesn't preserve value"


@given(st.floats(min_value=0, max_value=1e15, allow_nan=False, allow_infinity=False),
       st.text(min_size=0, max_size=5),
       st.integers(min_value=1, max_value=1024))
def test_format_sizeof_units(num, suffix, divisor):
    """Property: format_sizeof should format bytes with appropriate units"""
    result = tqdm.format_sizeof(num, suffix=suffix, divisor=divisor)
    assert isinstance(result, str), f"format_sizeof should return string, got {type(result)}"
    
    # Result should end with suffix if provided
    if suffix:
        assert result.endswith(suffix) or any(result.endswith(unit + suffix) 
                                              for unit in ['', 'k', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y'])


@given(st.integers(min_value=0, max_value=1000),
       st.integers(min_value=0, max_value=1000), 
       st.floats(min_value=0.001, max_value=1000, allow_nan=False, allow_infinity=False))
def test_format_meter_returns_string(n, total, elapsed):
    """Property: format_meter should always return a string"""
    result = tqdm.format_meter(n, total, elapsed)
    assert isinstance(result, str), f"format_meter should return string, got {type(result)}"
    
    # Check that percentage is included when total is known
    if total > 0:
        percentage = int(100 * n / total)
        assert f"{percentage}%" in result or f"{percentage:3d}%" in result


@given(st.integers(min_value=0, max_value=10000))
def test_close_is_idempotent(total):
    """Property: Calling close() multiple times should be safe"""
    old_stderr = sys.stderr
    sys.stderr = StringIO()
    try:
        t = tqdm(total=total)
        t.update(10)
    
        # Close multiple times - should not raise
        t.close()
        t.close()
        t.close()
    
        # After closing, n should still be accessible
        assert isinstance(t.n, int)
    finally:
        sys.stderr = old_stderr


@given(st.lists(st.integers(min_value=-1000, max_value=1000), min_size=0, max_size=100))
def test_update_with_negative_clamps_at_zero(updates):
    """Property: Progress should never go below 0"""
    old_stderr = sys.stderr
    sys.stderr = StringIO()
    try:
        t = tqdm(total=1000)
    
        for update_val in updates:
            t.update(update_val)
            assert t.n >= 0, f"Progress n={t.n} should never be negative"
    
        t.close()
    finally:
        sys.stderr = old_stderr


@given(st.integers(min_value=1, max_value=100))
def test_context_manager_closes_automatically(total):
    """Property: Using tqdm as context manager should close it automatically"""
    old_stderr = sys.stderr
    sys.stderr = StringIO()
    try:
        with tqdm(total=total) as t:
            t.update(1)
            n_inside = t.n
    
        # After context, the bar should be closed
        # We can't directly test if it's closed, but we can verify n is still accessible
        assert t.n == n_inside
    finally:
        sys.stderr = old_stderr