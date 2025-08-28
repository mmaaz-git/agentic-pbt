"""Demonstration of the complex number bug in troposphere.ses.boolean validator"""

import troposphere.ses as ses
from hypothesis import given, strategies as st


# Minimal failing example
def test_boolean_accepts_complex_minimal():
    """Boolean validator incorrectly accepts complex numbers"""
    # These should NOT be accepted by a boolean validator
    assert ses.boolean(0j) == False  # Bug: accepts complex zero
    assert ses.boolean(1+0j) == True  # Bug: accepts complex one
    
    # Even more complex examples work
    assert ses.boolean(0+0j) == False
    assert ses.boolean(complex(1, 0)) == True


# Property test that found the bug
@given(st.complex_numbers())
def test_boolean_rejects_complex(x):
    """Property: boolean validator should reject all complex numbers"""
    # A boolean validator should never accept complex numbers
    try:
        result = ses.boolean(x)
        # If we get here, a complex number was accepted
        if x == 0+0j or x == 1+0j:
            # These are the buggy cases
            print(f"BUG: boolean({x!r}) returned {result}")
        else:
            # Should never happen based on current implementation
            assert False, f"Unexpected complex accepted: {x!r}"
    except (ValueError, TypeError):
        # This is what we expect - complex numbers should be rejected
        pass


if __name__ == "__main__":
    test_boolean_accepts_complex_minimal()
    print("Confirmed: boolean validator accepts complex numbers 0j and 1+0j")