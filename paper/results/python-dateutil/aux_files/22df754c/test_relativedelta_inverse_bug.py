import datetime
from hypothesis import given, strategies as st, settings, note
from dateutil import relativedelta
import pytest


# More comprehensive test for relativedelta inverse issue
@given(
    st.dates(min_value=datetime.date(1900, 1, 1), max_value=datetime.date(2100, 12, 31)),
    st.integers(min_value=-24, max_value=24),
    st.integers(min_value=-100, max_value=100)
)
@settings(max_examples=1000)
def test_relativedelta_inverse_comprehensive(base_date, months, days):
    """Test that (date + rd) - rd == date for various combinations"""
    base = datetime.datetime.combine(base_date, datetime.time())
    rd = relativedelta.relativedelta(months=months, days=days)
    
    result = base + rd - rd
    
    if result != base:
        # Log the failure details
        note(f"Base: {base}")
        note(f"Relativedelta: {rd}")
        note(f"(base + rd): {base + rd}")
        note(f"(base + rd) - rd: {result}")
        note(f"Difference from base: {(result - base).days} days")
        
        # The property fails
        assert False, f"Inverse property violated: (base + rd) - rd != base"


# Simpler minimal reproduction
def test_relativedelta_inverse_minimal():
    """Minimal test case showing the inverse property failure"""
    base = datetime.datetime(2020, 6, 15)
    rd = relativedelta.relativedelta(months=1, days=-15)
    
    # Apply rd then reverse it
    result = base + rd - rd
    
    # This should equal base but doesn't
    assert result != base  # This passes, showing the bug
    assert result == datetime.datetime(2020, 6, 14)  # Off by one day!


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "--hypothesis-show-statistics"])