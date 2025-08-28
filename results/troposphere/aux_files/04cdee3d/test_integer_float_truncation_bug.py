"""Property-based test demonstrating integer validator bug with float truncation."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st
import pytest
from troposphere import validators


@given(st.floats(min_value=-1e10, max_value=1e10, allow_nan=False, allow_infinity=False).filter(lambda x: x != int(x)))
def test_integer_validator_accepts_non_integers(value):
    """
    Test that integer validator rejects non-integer floats.
    
    Property: The integer() validator should only accept values that are
    actual integers, not floats with fractional parts.
    
    Bug: The validator accepts any float that can be converted to int,
    silently truncating fractional parts.
    """
    
    # value is a float that's not equal to its integer conversion
    # (i.e., it has a fractional part)
    assert value != int(value)
    
    # The integer validator should reject this
    with pytest.raises(ValueError):
        validators.integer(value)


def test_demonstrate_float_truncation_bug():
    """Demonstrate the float truncation bug."""
    
    print("\n=== BUG DEMONSTRATION ===")
    print("The integer() validator incorrectly accepts non-integer floats,")
    print("silently truncating their fractional parts.\n")
    
    test_cases = [
        1.5,
        2.9,
        -3.1,
        100.999,
        0.1
    ]
    
    for value in test_cases:
        try:
            result = validators.integer(value)
            print(f"✗ BUG: integer({value}) returned {result} instead of raising ValueError")
            print(f"  Note: int({value}) = {int(value)} (truncation occurred)")
        except ValueError as e:
            print(f"✓ Correctly raised ValueError for {value}: {e}")
    
    print("\n=== NETWORK PORT IMPLICATIONS ===")
    print("This bug affects network_port() which uses integer() internally:\n")
    
    port_cases = [
        (80.5, 80),
        (443.9, 443),
        (8080.1, 8080),
        (65535.5, 65535),
        (65535.9, 65535)
    ]
    
    for float_port, truncated in port_cases:
        try:
            result = validators.network_port(float_port)
            print(f"✗ BUG: network_port({float_port}) accepted and returned {result}")
            print(f"  This treats port {float_port} as port {truncated} (incorrect!)")
        except ValueError as e:
            print(f"✓ Correctly rejected {float_port}: {e}")


if __name__ == "__main__":
    # First demonstrate the bug
    test_demonstrate_float_truncation_bug()
    
    print("\n=== RUNNING HYPOTHESIS TEST ===")
    # Then run the property-based test (which will fail, demonstrating the bug)
    pytest.main([__file__, "-v", "--tb=short", "-x"])