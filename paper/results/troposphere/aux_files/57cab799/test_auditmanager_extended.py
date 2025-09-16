#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import math
from hypothesis import given, strategies as st, settings, assume, example
from troposphere.auditmanager import *
from troposphere.validators import double


# More aggressive testing settings
test_settings = settings(max_examples=1000, deadline=None)


# Test with specific edge cases that might break double
@given(value=st.one_of(
    st.just(b'123.456'),
    st.just(b'inf'),
    st.just(b'-inf'),
    st.just(b'nan'),
    st.just(b'1e10'),
    st.just(bytearray(b'789.012')),
    st.just(bytearray(b'not_a_number')),
))
@test_settings
def test_double_bytes_edge_cases(value):
    """Test double function with specific byte/bytearray values"""
    try:
        result = double(value)
        # double accepts it, check if float also accepts
        float_val = float(value)
        # Both accept - consistent
    except ValueError as e1:
        # double rejects it, check if float also rejects
        try:
            float_val = float(value)
            # Float accepts but double rejects - INCONSISTENT!
            assert False, f"BUG: double() rejects {value!r} with '{e1}' but float() accepts it and returns {float_val}"
        except (ValueError, TypeError):
            # Both reject - consistent
            pass


# Test the from_dict bug I noticed with Scope
@given(
    accounts_data=st.lists(
        st.fixed_dictionaries({
            "Id": st.text(min_size=1),
            "Name": st.text(min_size=1),
        }),
        min_size=1,
        max_size=3
    )
)
@test_settings  
def test_scope_from_dict_bug(accounts_data):
    """Test if Scope.from_dict works correctly with nested structures"""
    # Create a Scope using normal constructor
    accounts = [AWSAccount(**data) for data in accounts_data]
    scope1 = Scope(AwsAccounts=accounts)
    
    # Get dict representation
    dict_repr = scope1.to_dict()
    
    # Try to recreate using from_dict (this should work but might not)
    try:
        # This is how from_dict should work according to the base class
        scope2 = Scope.from_dict(None, dict_repr)
        dict_repr2 = scope2.to_dict()
        
        # They should be equal
        assert dict_repr == dict_repr2, f"from_dict round-trip failed: {dict_repr} != {dict_repr2}"
    except Exception as e:
        # If this fails, it's likely a bug in from_dict for nested structures
        error_msg = str(e)
        if "unexpected keyword argument" in error_msg:
            # This is the bug I suspected - from_dict doesn't handle nested props correctly
            assert False, f"BUG: Scope.from_dict() fails with nested properties: {e}"
        else:
            # Some other error
            raise


# Test Assessment with all possible fields
@given(
    name=st.text(min_size=1),
    description=st.one_of(st.none(), st.text()),
    status=st.one_of(st.none(), st.sampled_from(["ACTIVE", "INACTIVE", "PENDING"])),
    framework_id=st.one_of(st.none(), st.text())
)
@test_settings
def test_assessment_complete_roundtrip(name, description, status, framework_id):
    """Test Assessment with various combinations of fields"""
    data = {"Name": name}
    if description is not None:
        data["Description"] = description
    if status is not None:
        data["Status"] = status
    if framework_id is not None:
        data["FrameworkId"] = framework_id
        
    assessment1 = Assessment("Test", **data)
    dict_repr = assessment1.to_dict()
    
    # Should be able to recreate from dict
    assessment2 = Assessment.from_dict("Test", dict_repr["Properties"])
    dict_repr2 = assessment2.to_dict()
    
    assert dict_repr == dict_repr2


# Test double with strings that look like numbers
@given(s=st.text())
@example(s="1.0")
@example(s="123")
@example(s="-456.789")
@example(s="1e10")
@example(s="inf")
@example(s="-inf")
@example(s="nan")
@example(s="NaN")
@example(s="Infinity")
@example(s="+123")
@example(s="  123  ")  # with spaces
@example(s="123\\n")  # with newline
@test_settings
def test_double_string_consistency(s):
    """Test that double and float have consistent behavior for strings"""
    double_error = None
    float_error = None
    
    try:
        double_result = double(s)
    except ValueError as e:
        double_error = e
    
    try:
        float_result = float(s)
    except ValueError as e:
        float_error = e
    
    # Both should either succeed or fail
    if double_error is None and float_error is not None:
        assert False, f"BUG: double({s!r}) succeeds but float({s!r}) fails with {float_error}"
    elif double_error is not None and float_error is None:
        assert False, f"BUG: double({s!r}) fails but float({s!r}) succeeds returning {float_result}"


# Test with extreme numeric values
@given(x=st.one_of(
    st.just(sys.float_info.max * 2),  # overflow
    st.just(sys.float_info.min / 2),  # underflow  
    st.floats(min_value=1e308, max_value=1e309),  # near overflow
    st.floats(allow_nan=True, allow_infinity=True),
))
@test_settings
def test_double_extreme_values(x):
    """Test double with extreme numeric values"""
    try:
        result = double(x)
        # Should preserve the value exactly
        assert result is x
    except ValueError:
        # Should only fail if float() would also fail
        try:
            float(x)
            assert False, f"double rejects {x} but float accepts it"
        except (ValueError, TypeError, OverflowError):
            pass


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short", "-x"])  # -x stops on first failure