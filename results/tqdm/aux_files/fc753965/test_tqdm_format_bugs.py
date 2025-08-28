import math
import re
from hypothesis import assume, given, strategies as st, settings
import tqdm


@given(st.floats(allow_nan=False, allow_infinity=False))
def test_format_sizeof_with_zero(num):
    """Test format_sizeof behavior with zero and near-zero values."""
    # Documentation says "Number ( >= 1) to format"
    # But what happens with 0 or values between 0 and 1?
    
    if 0 <= num < 1:
        # This violates the documented precondition
        formatted = tqdm.tqdm.format_sizeof(num)
        # Check if it handles gracefully or produces unexpected output
        assert isinstance(formatted, str)
        
        # For zero specifically
        if num == 0:
            # Zero bytes should probably be "0.00B" or similar
            assert '0' in formatted


@given(st.floats(min_value=1, max_value=1e100))
def test_format_sizeof_suffix_consistency(num):
    """Test that format_sizeof consistently includes the suffix."""
    # Test with various suffixes
    suffixes = ['B', 'iB', 'Hz', 'bps', '']
    
    for suffix in suffixes:
        formatted = tqdm.tqdm.format_sizeof(num, suffix=suffix)
        
        if suffix:
            # The suffix should appear in the output
            assert suffix in formatted, f"Suffix '{suffix}' not in output '{formatted}' for num={num}"


@given(st.integers(min_value=-2147483648, max_value=-1))
def test_format_interval_negative_robust(seconds):
    """Test format_interval with negative seconds more thoroughly."""
    formatted = tqdm.tqdm.format_interval(seconds)
    
    # Should return a string
    assert isinstance(formatted, str)
    
    # Check if it produces sensible output for negative times
    # The function signature says "t : int Number of seconds" with no mention of >= 0
    # So negative values should either be handled or documented as invalid
    
    # Look for signs of incorrect handling
    if '-' not in formatted and seconds < 0:
        # If negative sign is missing, this might be a bug
        # Check if it's wrapping around or doing modulo arithmetic
        positive_formatted = tqdm.tqdm.format_interval(abs(seconds))
        if formatted == positive_formatted:
            # Same output for negative and positive - potential bug!
            assert False, f"format_interval({seconds}) == format_interval({abs(seconds)}) = '{formatted}'"


@given(st.integers())
def test_format_interval_overflow(seconds):
    """Test format_interval with very large values that might overflow."""
    formatted = tqdm.tqdm.format_interval(seconds)
    
    # Should always return a string
    assert isinstance(formatted, str)
    
    # Check format is still [H:]MM:SS
    if seconds >= 0:
        # Should have colons
        assert ':' in formatted
        
        # Check the parts
        parts = formatted.split(':')
        
        # Should have at least MM:SS
        assert len(parts) >= 2
        
        # Last part (seconds) should be 2 digits
        assert len(parts[-1]) == 2, f"Seconds should be 2 digits, got '{parts[-1]}' in '{formatted}'"
        
        # Second to last (minutes) should be 2 digits  
        assert len(parts[-2]) == 2, f"Minutes should be 2 digits, got '{parts[-2]}' in '{formatted}'"
        
        # If there are hours, they can be any number of digits
        if len(parts) == 3:
            assert parts[0].isdigit() or (parts[0][0] == '-' and parts[0][1:].isdigit())


@given(st.integers(min_value=0, max_value=2147483647))
def test_format_interval_round_trip_precise(seconds):
    """Test precise round-trip for format_interval."""
    formatted = tqdm.tqdm.format_interval(seconds)
    
    # Parse it back
    pattern = r'^(?:(\d+):)?(\d{2}):(\d{2})$'
    match = re.match(pattern, formatted)
    
    assert match is not None, f"Format '{formatted}' doesn't match expected pattern"
    
    groups = match.groups()
    if groups[0] is not None:
        hours = int(groups[0])
        minutes = int(groups[1])
        secs = int(groups[2])
    else:
        hours = 0
        minutes = int(groups[1])
        secs = int(groups[2])
    
    parsed = hours * 3600 + minutes * 60 + secs
    
    # Should match exactly
    assert parsed == seconds, f"Round-trip failed: {seconds} -> '{formatted}' -> {parsed}"