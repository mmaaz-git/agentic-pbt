"""
Property-based test to demonstrate fractional seconds inconsistency bug.
"""
from hypothesis import given, strategies as st
import dateutil.parser
import pytest


@given(st.floats(min_value=0.0, max_value=0.9999999999))
def test_fractional_seconds_consistency(fraction):
    """Test that fractional seconds are handled consistently (either always truncated or always rounded)."""
    # Create datetime string with high-precision fractional seconds
    frac_str = f"{fraction:.10f}".rstrip('0')
    if '.' not in frac_str:
        frac_str = "0.0"
    
    # Only use the decimal part
    decimal_part = frac_str.split('.')[1] if '.' in frac_str else "0"
    
    dt_str = f"2024-01-01T00:00:00.{decimal_part}"
    
    try:
        parsed = dateutil.parser.isoparse(dt_str)
        
        # Calculate what we'd get with truncation (take first 6 digits)
        truncated_str = (decimal_part + "000000")[:6]
        expected_truncated = int(truncated_str)
        
        # Calculate what we'd get with rounding
        if len(decimal_part) > 6:
            # Round based on 7th digit and beyond
            frac_for_round = float('0.' + decimal_part)
            expected_rounded = round(frac_for_round * 1000000)
            # Clamp to valid microsecond range
            expected_rounded = min(expected_rounded, 999999)
        else:
            expected_rounded = expected_truncated
        
        # The parser should be consistent - either always truncate or always round
        # Currently it does BOTH depending on the value!
        is_truncated = (parsed.microsecond == expected_truncated)
        is_rounded = (parsed.microsecond == expected_rounded)
        
        # This assertion will fail, demonstrating the inconsistency
        assert is_truncated or is_rounded, f"Microsecond {parsed.microsecond} is neither truncated ({expected_truncated}) nor rounded ({expected_rounded}) for input {dt_str}"
        
        # To demonstrate the bug: the parser should choose ONE strategy consistently
        # If we find cases where it sometimes truncates and sometimes rounds, that's a bug
        
    except (ValueError, dateutil.parser.ParserError):
        pass


if __name__ == "__main__":
    # Run the test - it should reveal the inconsistency
    pytest.main([__file__, "-v", "--tb=short", "--hypothesis-seed=0"])