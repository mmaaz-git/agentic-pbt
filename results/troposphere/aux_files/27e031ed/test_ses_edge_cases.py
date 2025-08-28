"""Deep property testing for troposphere.ses validators - looking for edge cases"""

import math
from hypothesis import given, strategies as st, assume, settings
import troposphere.ses as ses


# Test boolean with various string cases
@given(st.text())
def test_boolean_case_sensitivity(s):
    """Test case sensitivity in boolean parsing"""
    # The implementation accepts "true", "True", "false", "False"
    # But what about "TRUE", "FALSE", "TrUe", etc?
    if s.lower() in ["true", "false", "0", "1"]:
        # These should potentially work
        try:
            result = ses.boolean(s)
            # Check if case variants are handled consistently
            if s.lower() == "true" and s not in ["true", "True", "1"]:
                # Found a case variant that might not be handled
                assert False, f"Unexpected case variant accepted: {s!r}"
            if s.lower() == "false" and s not in ["false", "False", "0"]:
                assert False, f"Unexpected case variant accepted: {s!r}"
        except ValueError:
            # Check if this should have been accepted
            if s in ["true", "True", "false", "False", "0", "1"]:
                assert False, f"Should have accepted {s!r}"


# Test boolean with numeric edge cases
@given(st.one_of(
    st.floats(),
    st.integers(),
    st.complex_numbers(),
))
def test_boolean_numeric_edge_cases(x):
    """Test boolean with various numeric types"""
    try:
        result = ses.boolean(x)
        # Only 0 and 1 should be accepted as numbers
        if isinstance(x, (int, float)) and x in [0, 1]:
            assert result == bool(x)
        else:
            assert False, f"Unexpected numeric value accepted: {x!r}"
    except (ValueError, TypeError):
        # Expected for non 0/1 numbers
        pass


# Test double with string representations
@given(st.text())
@settings(max_examples=500)
def test_double_string_parsing(s):
    """Test double's string parsing capabilities"""
    try:
        result = ses.double(s)
        # If it succeeds, float(s) should also succeed
        float_val = float(s)
        # And float(result) should equal float(s)
        assert float(result) == float_val
    except ValueError:
        # If ses.double fails, float should also fail (or the string is invalid)
        try:
            float(s)
            # If float succeeds but ses.double failed, that's interesting
            assert False, f"float() accepts {s!r} but double() doesn't"
        except (ValueError, TypeError):
            pass  # Both failed, as expected


# Test double with bytes/bytearray
@given(st.one_of(
    st.binary(),
    st.binary().map(bytearray)
))
def test_double_bytes_types(b):
    """Test double with bytes and bytearray"""
    try:
        result = ses.double(b)
        # If it succeeds, conversion to float should work
        float_val = float(result)
        # The result should be the same as directly converting
        if isinstance(b, (bytes, bytearray)):
            # Check if Python's float() would accept this
            try:
                expected = float(b)
                assert float_val == expected
            except (ValueError, TypeError):
                # ses.double accepted something float() doesn't?
                assert False, f"double() accepts {b!r} but float() doesn't"
    except (ValueError, TypeError):
        pass  # Expected for most binary data


# Test for None and other special values
@given(st.one_of(
    st.none(),
    st.just(NotImplemented),
    st.just(Ellipsis),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.integers()),
))
def test_validators_special_types(x):
    """Test validators with special Python types"""
    # Boolean validator
    try:
        bool_result = ses.boolean(x)
        # If it succeeds, check if it makes sense
        if x not in [True, False, 0, 1]:
            assert False, f"boolean() unexpectedly accepted {x!r}"
    except (ValueError, TypeError, AttributeError):
        pass  # Expected
    
    # Double validator
    try:
        double_result = ses.double(x)
        # If it succeeds, check if float conversion works
        float_val = float(double_result)
    except (ValueError, TypeError, AttributeError):
        pass  # Expected


# Test whitespace handling
@given(st.text(alphabet=" \t\n\r0123456789.-+eE"))
def test_double_whitespace_handling(s):
    """Test how double handles whitespace in numeric strings"""
    try:
        result = ses.double(s)
        # If double accepts it, float should too
        float_val = float(result)
        
        # Compare with Python's float() directly
        try:
            expected = float(s)
            assert float_val == expected
        except ValueError:
            # double accepted something float doesn't?
            if s.strip():  # If there's actual content
                assert False, f"double() accepts {s!r} but float() doesn't"
    except ValueError:
        pass  # Expected for invalid strings


# Test integer/float boundary cases  
@given(st.integers(min_value=-10**308, max_value=10**308))
def test_double_large_integers(x):
    """Test double with very large integers"""
    try:
        result = ses.double(x)
        assert result == x
        # Should be convertible to float
        float_val = float(result)
        # For large integers, might lose precision but shouldn't fail
        if abs(x) < 2**53:  # Within float precision range
            assert float_val == float(x)
    except (ValueError, OverflowError):
        pass  # Expected for very large numbers