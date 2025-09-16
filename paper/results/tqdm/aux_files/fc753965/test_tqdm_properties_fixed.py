import math
import re
import io
from hypothesis import assume, given, strategies as st, settings
import tqdm


@given(st.integers(min_value=0, max_value=359999))  # Up to 99:59:59
def test_format_interval_parsing(seconds):
    """Test that format_interval produces parseable time strings."""
    formatted = tqdm.tqdm.format_interval(seconds)
    
    # The docstring claims format is [H:]MM:SS
    # Let's verify this format and check we can parse it back
    pattern = r'^(?:(\d+):)?(\d{2}):(\d{2})$'
    match = re.match(pattern, formatted)
    assert match is not None, f"Format {formatted} doesn't match [H:]MM:SS pattern"
    
    # Parse back the time
    groups = match.groups()
    if groups[0] is not None:
        hours = int(groups[0])
        minutes = int(groups[1])
        secs = int(groups[2])
    else:
        hours = 0
        minutes = int(groups[1])
        secs = int(groups[2])
    
    parsed_seconds = hours * 3600 + minutes * 60 + secs
    assert parsed_seconds == seconds, f"Round-trip failed: {seconds} -> {formatted} -> {parsed_seconds}"


@given(st.floats(allow_nan=False, allow_infinity=False, min_value=-1e308, max_value=1e308))
def test_format_num_properties(n):
    """Test format_num scientific notation properties."""
    formatted = tqdm.tqdm.format_num(n)
    
    # Should return a string
    assert isinstance(formatted, str)
    
    # Should be parseable as a float (unless it's using special notation)
    if 'e' in formatted.lower() or '.' in formatted or formatted.lstrip('-').isdigit():
        try:
            parsed = float(formatted)
            # Check if parsing is approximately correct (considering .3g precision)
            if n != 0:
                relative_error = abs((parsed - n) / n)
                # .3g gives 3 significant figures, so relative error should be < 0.1%
                assert relative_error < 0.01 or abs(parsed - n) < 1e-10
        except ValueError:
            # Some edge cases might produce non-standard notation
            pass


@given(st.floats(min_value=1.0, max_value=1e15, allow_nan=False, allow_infinity=False))
def test_format_sizeof_invariants(num):
    """Test format_sizeof SI prefix formatting invariants."""
    formatted = tqdm.tqdm.format_sizeof(num, suffix='B')
    
    # Should return a string
    assert isinstance(formatted, str)
    
    # Should contain the suffix
    assert 'B' in formatted
    
    # Test with different divisors
    formatted_1000 = tqdm.tqdm.format_sizeof(num, divisor=1000)
    formatted_1024 = tqdm.tqdm.format_sizeof(num, divisor=1024)
    
    # Both should be strings
    assert isinstance(formatted_1000, str)
    assert isinstance(formatted_1024, str)
    
    # Test monotonicity: larger numbers should not have smaller prefixes
    if num >= 1000:
        smaller_num = num / 10
        formatted_smaller = tqdm.tqdm.format_sizeof(smaller_num, suffix='B')
        # This is a weak test but checks basic consistency
        assert isinstance(formatted_smaller, str)


@given(st.integers(min_value=0, max_value=10000))
def test_tqdm_counter_update_invariants(total):
    """Test tqdm counter update invariants."""
    # Create a progress bar with output to StringIO to avoid terminal output
    pbar = tqdm.tqdm(total=total, file=io.StringIO())
    
    try:
        # Initial state should be 0
        assert pbar.n == 0
        
        # Update by 1
        pbar.update(1)
        assert pbar.n == 1
        
        # Update by arbitrary amount
        if total > 10:
            update_amount = min(5, total - 1)
            pbar.update(update_amount)
            assert pbar.n == 1 + update_amount
        
        # Reset should go back to 0
        pbar.reset()
        assert pbar.n == 0
        
        # Update with negative should still work (going backwards)
        pbar.update(10)
        assert pbar.n == 10
        pbar.update(-5)
        assert pbar.n == 5
        
    finally:
        pbar.close()


@given(st.lists(st.integers(min_value=-100, max_value=100), min_size=1, max_size=20))
def test_tqdm_update_sum_property(updates):
    """Test that sum of updates equals final counter value."""
    pbar = tqdm.tqdm(file=io.StringIO())
    
    try:
        for update in updates:
            pbar.update(update)
        
        expected_total = sum(updates)
        assert pbar.n == expected_total, f"Sum of updates {sum(updates)} != counter {pbar.n}"
        
    finally:
        pbar.close()


@given(st.integers(min_value=0, max_value=1000))
def test_tqdm_reset_with_new_total(new_total):
    """Test reset with new total parameter."""
    pbar = tqdm.tqdm(total=100, file=io.StringIO())
    
    try:
        # Update to some value
        pbar.update(50)
        assert pbar.n == 50
        
        # Reset with new total
        pbar.reset(total=new_total)
        assert pbar.n == 0
        assert pbar.total == new_total
        
    finally:
        pbar.close()


@given(st.floats(min_value=0.0, max_value=1000.0, allow_nan=False, allow_infinity=False))
def test_tqdm_float_updates(update_value):
    """Test that tqdm handles float updates correctly."""
    pbar = tqdm.tqdm(file=io.StringIO())
    
    try:
        pbar.update(update_value)
        assert math.isclose(pbar.n, update_value, rel_tol=1e-9)
        
        pbar.update(update_value)
        assert math.isclose(pbar.n, 2 * update_value, rel_tol=1e-9)
        
    finally:
        pbar.close()


@given(st.integers(min_value=0, max_value=86400*365))  # Up to a year in seconds
def test_format_interval_large_values(seconds):
    """Test format_interval with larger time values."""
    formatted = tqdm.tqdm.format_interval(seconds)
    
    # Should always return a string
    assert isinstance(formatted, str)
    
    # Should contain colons for time separation
    assert ':' in formatted
    
    # Minutes and seconds should be 2 digits
    parts = formatted.split(':')
    assert len(parts[-1]) == 2  # seconds
    assert len(parts[-2]) == 2  # minutes