import math
import io
from hypothesis import assume, given, strategies as st, settings, example
import tqdm


@given(st.floats(min_value=-1e10, max_value=1e10, allow_nan=True, allow_infinity=True))
def test_format_num_edge_cases(n):
    """Test format_num with all possible float values."""
    result = tqdm.tqdm.format_num(n)
    
    # Should always return a string
    assert isinstance(result, str)
    
    # For regular numbers, check if it's parseable
    if not (math.isnan(n) or math.isinf(n)):
        # Try to parse it back
        try:
            parsed = float(result)
            # For non-zero values, check relative accuracy
            if n != 0:
                rel_error = abs((parsed - n) / n)
                # .3g format should give at least 3 significant figures
                # But very small or very large numbers might lose precision
                if abs(n) > 1e-100 and abs(n) < 1e100:
                    assert rel_error < 0.01 or abs(parsed - n) < 1e-10
        except ValueError:
            # Some formats might not be parseable (like "1.23k")
            pass


@given(st.integers(min_value=-9223372036854775808, max_value=9223372036854775807))
def test_format_interval_extreme_values(seconds):
    """Test format_interval with 64-bit integer range."""
    result = tqdm.tqdm.format_interval(seconds)
    
    # Should always return a string
    assert isinstance(result, str)
    
    # Should contain time separators
    assert ':' in result
    
    # For very large values, hours can be huge
    parts = result.split(':')
    assert len(parts) >= 2  # At least MM:SS
    
    # Minutes and seconds should be 00-59
    if len(parts) >= 2:
        minutes = parts[-2]
        seconds_str = parts[-1]
        
        # Should be 2 digits
        assert len(minutes) == 2
        assert len(seconds_str) == 2
        
        # Should be valid ranges (unless negative handling is broken)
        if seconds >= 0:
            assert 0 <= int(minutes) <= 59
            assert 0 <= int(seconds_str) <= 59


@given(st.floats(min_value=0.99, max_value=1.01, exclude_min=False, exclude_max=False))
def test_format_sizeof_boundary(num):
    """Test format_sizeof around the boundary value of 1."""
    # Documentation says num should be >= 1
    result = tqdm.tqdm.format_sizeof(num, suffix='B')
    
    # Should return a string
    assert isinstance(result, str)
    
    # Should contain the suffix
    assert 'B' in result
    
    # Near 1, should show as "1.00B" or similar
    if 0.995 <= num <= 1.005:
        assert '1' in result or '0.99' in result or '1.00' in result or '1.01' in result


@given(st.lists(st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False),
                min_size=100, max_size=200))
def test_tqdm_large_update_sequence(updates):
    """Test tqdm with many updates for numerical stability."""
    pbar = tqdm.tqdm(file=io.StringIO())
    
    try:
        # Track the sum ourselves for comparison
        expected_sum = 0.0
        
        for update in updates:
            pbar.update(update)
            expected_sum += update
        
        # Check if the internal counter matches our sum (with float tolerance)
        assert math.isclose(pbar.n, expected_sum, rel_tol=1e-9, abs_tol=1e-9)
        
    finally:
        pbar.close()


@given(st.integers(min_value=1, max_value=100000),
       st.integers(min_value=1, max_value=100))
def test_format_meter_progress_consistency(total, n_updates):
    """Test that format_meter produces consistent progress representations."""
    n_values = [i * total // n_updates for i in range(n_updates + 1)]
    
    outputs = []
    for n in n_values:
        output = tqdm.tqdm.format_meter(
            n=n,
            total=total,
            elapsed=1.0
        )
        outputs.append((n, output))
    
    # Check that progress increases monotonically in the output
    for i in range(len(outputs) - 1):
        n1, out1 = outputs[i]
        n2, out2 = outputs[i + 1]
        
        # Extract percentage if present
        import re
        pct_pattern = r'(\d+)%'
        
        match1 = re.search(pct_pattern, out1)
        match2 = re.search(pct_pattern, out2)
        
        if match1 and match2:
            pct1 = int(match1.group(1))
            pct2 = int(match2.group(1))
            
            # Percentage should increase or stay same
            assert pct2 >= pct1, f"Percentage decreased: {pct1}% -> {pct2}% for n={n1} -> n={n2}"


@given(st.floats(min_value=1e-100, max_value=1e100, allow_nan=False, allow_infinity=False))
def test_format_sizeof_divisor_consistency(num):
    """Test that different divisors produce consistent results."""
    # Test with both common divisors
    result_1000 = tqdm.tqdm.format_sizeof(num, suffix='B', divisor=1000)
    result_1024 = tqdm.tqdm.format_sizeof(num, suffix='B', divisor=1024)
    
    # Both should be strings
    assert isinstance(result_1000, str)
    assert isinstance(result_1024, str)
    
    # Both should contain the suffix
    assert 'B' in result_1000
    assert 'B' in result_1024
    
    # Extract the numeric part and prefix
    import re
    pattern = r'([\d.]+)\s*([KMGTPEZY]?)B'
    
    match_1000 = re.search(pattern, result_1000)
    match_1024 = re.search(pattern, result_1024)
    
    if match_1000 and match_1024:
        val_1000 = float(match_1000.group(1))
        val_1024 = float(match_1024.group(1))
        prefix_1000 = match_1000.group(2)
        prefix_1024 = match_1024.group(2)
        
        # With divisor=1024, the displayed value should generally be smaller
        # for the same prefix (since 1024 > 1000)
        if prefix_1000 == prefix_1024 and prefix_1000:
            # Same prefix means divisor=1024 should show larger number
            # (because it takes more to reach the next prefix)
            assert val_1024 >= val_1000 * 0.9  # Allow some tolerance