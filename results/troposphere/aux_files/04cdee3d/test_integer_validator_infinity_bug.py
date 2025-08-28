"""Property-based test demonstrating integer validator bug with infinity values."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st
import pytest
from troposphere import validators


@given(st.sampled_from([float('inf'), float('-inf')]))
def test_integer_validator_infinity_handling(value):
    """
    Test that integer validator properly handles infinity values.
    
    Property: The integer() validator should raise ValueError for all 
    invalid inputs, maintaining a consistent error interface.
    
    Bug: The validator raises OverflowError for infinity values instead
    of ValueError, breaking the expected error contract.
    """
    
    # The integer validator should raise ValueError for invalid inputs
    # according to its implementation at line 50 of validators/__init__.py:
    # raise ValueError("%r is not a valid integer" % x)
    
    # However, it calls int(x) which can raise OverflowError for infinity
    with pytest.raises(ValueError):
        validators.integer(value)


# Demonstrate the actual behavior
def test_demonstrate_bug():
    """Demonstrate the actual buggy behavior."""
    
    print("\n=== BUG DEMONSTRATION ===")
    print("The integer() validator claims to raise ValueError for invalid inputs")
    print("but actually raises OverflowError for infinity values.\n")
    
    # Test with infinity
    try:
        validators.integer(float('inf'))
        print("ERROR: Should have raised an exception!")
    except ValueError as e:
        print(f"✓ Correctly raised ValueError: {e}")
    except OverflowError as e:
        print(f"✗ BUG: Raised OverflowError instead of ValueError: {e}")
    
    # Test with negative infinity
    try:
        validators.integer(float('-inf'))
        print("ERROR: Should have raised an exception!")
    except ValueError as e:
        print(f"✓ Correctly raised ValueError: {e}")
    except OverflowError as e:
        print(f"✗ BUG: Raised OverflowError instead of ValueError: {e}")
    
    # For comparison, test with NaN (which works correctly)
    print("\nFor comparison, NaN handling works correctly:")
    try:
        validators.integer(float('nan'))
        print("ERROR: Should have raised an exception!")
    except ValueError as e:
        print(f"✓ Correctly raised ValueError: {e}")
    except OverflowError as e:
        print(f"✗ BUG: Raised OverflowError instead of ValueError: {e}")


if __name__ == "__main__":
    # First demonstrate the bug
    test_demonstrate_bug()
    
    print("\n=== RUNNING HYPOTHESIS TEST ===")
    # Then run the property-based test (which will fail, demonstrating the bug)
    pytest.main([__file__, "-v", "--tb=short", "-x"])