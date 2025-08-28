#!/usr/bin/env python3
"""
Hypothesis test to confirm the validate_and_convert bug
"""
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/htmldate_env/lib/python3.13/site-packages')

from datetime import datetime
from hypothesis import given, strategies as st, settings, example

# Import the module
from htmldate import validators

# Strategy for valid date strings
valid_date_strings = st.builds(
    lambda y, m, d: f"{y:04d}-{m:02d}-{d:02d}",
    st.integers(min_value=2000, max_value=2024),
    st.integers(min_value=1, max_value=12),
    st.integers(min_value=1, max_value=28)  # Avoid month-end issues
)

@given(date_string=valid_date_strings)
@example(date_string="2024-01-15")  # Specific example
@settings(max_examples=10)
def test_validate_and_convert_with_strings(date_string):
    """Test that validate_and_convert fails with string inputs"""
    outputformat = "%Y-%m-%d"
    earliest = datetime(1995, 1, 1)
    latest = datetime(2030, 12, 31)
    
    # First check if date is valid
    is_valid = validators.is_valid_date(date_string, outputformat, earliest, latest)
    
    if is_valid:
        # This should raise AttributeError due to the bug
        try:
            result = validators.validate_and_convert(date_string, outputformat, earliest, latest)
            # If we get here, the bug might be fixed or we hit an edge case
            print(f"Unexpected success with '{date_string}': {result}")
            assert False, f"Expected AttributeError but got result: {result}"
        except AttributeError as e:
            # This is the expected bug
            assert "strftime" in str(e), f"Unexpected AttributeError: {e}"
            return True  # Bug confirmed
        except ValueError:
            # Some dates might fail for other reasons
            pass
    
    return False

if __name__ == "__main__":
    print("Running Hypothesis test to confirm bug...")
    print("-" * 50)
    
    try:
        # Run the test
        test_validate_and_convert_with_strings()
        print("\n✗ Test passed without finding the bug (unexpected)")
    except AssertionError as e:
        if "Expected AttributeError" in str(e):
            print("\n✗ Function didn't raise AttributeError (bug might be fixed)")
        else:
            print(f"\n✓ BUG CONFIRMED via Hypothesis testing")
            print(f"  The validate_and_convert function has a bug with string inputs")
            print(f"  Error: {e}")
    except Exception as e:
        print(f"\n✓ BUG CONFIRMED: {type(e).__name__}: {e}")
    
    # Also run a simple direct test
    print("\n" + "-" * 50)
    print("Direct test with known input:")
    try:
        result = validators.validate_and_convert("2024-01-15", "%Y-%m-%d", 
                                                datetime(2020, 1, 1), 
                                                datetime(2025, 12, 31))
        print(f"  Result: {result}")
    except AttributeError as e:
        print(f"  ✓ AttributeError confirmed: {e}")