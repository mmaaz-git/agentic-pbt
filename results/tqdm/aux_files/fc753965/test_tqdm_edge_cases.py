import math
import re
import io
from hypothesis import assume, given, strategies as st, settings
import tqdm


@given(st.integers())
def test_format_interval_negative_edge_case(seconds):
    """Test format_interval with negative values (undefined behavior)."""
    formatted = tqdm.tqdm.format_interval(seconds)
    
    # Should always return a string
    assert isinstance(formatted, str)
    
    # For negative values, check if it handles them gracefully
    if seconds < 0:
        # Should either handle negative gracefully or at least not crash
        assert formatted is not None


@given(st.floats(allow_nan=True, allow_infinity=True))
def test_format_num_special_values(n):
    """Test format_num with special float values."""
    formatted = tqdm.tqdm.format_num(n)
    
    # Should always return a string
    assert isinstance(formatted, str)
    
    # Check special cases
    if math.isnan(n):
        assert 'nan' in formatted.lower() or 'NaN' in formatted
    elif math.isinf(n):
        assert 'inf' in formatted.lower() or 'Inf' in formatted


@given(st.floats(min_value=-1e10, max_value=0.999999, exclude_min=False))
def test_format_sizeof_negative_and_small(num):
    """Test format_sizeof with values it's not designed for (< 1)."""
    # Docstring says "Number ( >= 1) to format" so test edge cases
    formatted = tqdm.tqdm.format_sizeof(num)
    
    # Should still return a string (graceful handling)
    assert isinstance(formatted, str)


@given(st.lists(st.floats(allow_nan=False, allow_infinity=False, min_value=-1e6, max_value=1e6), 
                min_size=1, max_size=100))
def test_tqdm_accumulated_float_precision(updates):
    """Test accumulated floating point precision in updates."""
    pbar = tqdm.tqdm(file=io.StringIO())
    
    try:
        # Apply all updates
        for update in updates:
            pbar.update(update)
        
        # Calculate expected sum carefully
        expected = sum(updates)
        
        # Check if the accumulated value is close (accounting for float precision)
        assert math.isclose(pbar.n, expected, rel_tol=1e-9, abs_tol=1e-9)
        
    finally:
        pbar.close()


@given(st.integers(min_value=1, max_value=10),
       st.lists(st.floats(min_value=0.1, max_value=10.0, allow_nan=False), min_size=1, max_size=20))
def test_tqdm_percentage_calculation(total, updates):
    """Test that percentage calculations are consistent."""
    total_float = float(total)
    pbar = tqdm.tqdm(total=total_float, file=io.StringIO())
    
    try:
        cumulative = 0.0
        for update in updates:
            pbar.update(update)
            cumulative += update
            
            # Check internal state
            if pbar.total and pbar.total > 0:
                percentage = (pbar.n / pbar.total) * 100
                expected_percentage = min((cumulative / total_float) * 100, 100)
                assert math.isclose(percentage, expected_percentage, rel_tol=1e-9)
        
    finally:
        pbar.close()


@given(st.text(min_size=0, max_size=100))
def test_tqdm_description_handling(description):
    """Test that tqdm handles various description strings correctly."""
    pbar = tqdm.tqdm(desc=description, file=io.StringIO())
    
    try:
        # Description should be stored correctly
        assert pbar.desc == description
        
        # Should be able to update it
        new_desc = description + "_updated" if description else "updated"
        pbar.set_description(new_desc)
        assert pbar.desc == new_desc
        
    finally:
        pbar.close()


@given(st.integers(min_value=-1000, max_value=1000))
def test_format_meter_with_negative_n(n):
    """Test format_meter static method with negative n values."""
    # format_meter is a static method that formats the progress bar
    try:
        result = tqdm.tqdm.format_meter(
            n=n,
            total=100,
            elapsed=1.0
        )
        # Should return a string
        assert isinstance(result, str)
        
        # For negative n, should still produce valid output
        if n < 0:
            # Should handle gracefully
            assert result is not None
            
    except Exception as e:
        # If it raises an exception for negative n, that's a potential bug
        if n < 0:
            assert False, f"format_meter failed with negative n={n}: {e}"
        else:
            raise


@given(st.floats(min_value=0.0, max_value=1e100, allow_infinity=False, allow_nan=False))
def test_format_sizeof_extreme_values(num):
    """Test format_sizeof with extremely large values."""
    formatted = tqdm.tqdm.format_sizeof(num, suffix='B')
    
    # Should return a string
    assert isinstance(formatted, str)
    
    # Should contain the suffix
    assert 'B' in formatted
    
    # For very large numbers, should use appropriate SI prefixes
    if num >= 1e24:  # Yotta
        assert 'Y' in formatted or 'e' in formatted  # Either YB or scientific notation
    elif num >= 1e21:  # Zetta  
        assert 'Z' in formatted or 'Y' in formatted or 'e' in formatted
        

@given(st.integers(min_value=1, max_value=1000000))
def test_tqdm_iterable_length_consistency(length):
    """Test that tqdm correctly handles iterables of known length."""
    data = list(range(length))
    
    # Create tqdm with iterable
    pbar = tqdm.tqdm(data, file=io.StringIO())
    
    try:
        # Total should be set to length of iterable
        assert pbar.total == length
        
        # Iterate through all items
        count = 0
        for item in pbar:
            count += 1
            # Current position should match count
            assert pbar.n == count
        
        # Should have processed all items
        assert count == length
        assert pbar.n == length
        
    finally:
        pbar.close()