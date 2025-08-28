#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, settings, assume, seed
from troposphere.auditmanager import *
from troposphere.validators import double
import traceback

# Use a specific seed for reproducibility
@seed(12345)
@settings(max_examples=5000, deadline=None)
@given(
    val=st.one_of(
        st.binary(min_size=1, max_size=100),
        st.text(min_size=1, max_size=100),
        st.floats(allow_nan=True, allow_infinity=True),
        st.integers(),
        st.booleans(),
        st.lists(st.integers()),
        st.dictionaries(st.text(), st.integers()),
        st.none(),
    )
)
def test_double_consistency_exhaustive(val):
    """Exhaustively test double vs float consistency"""
    double_result = None
    double_error = None
    float_result = None
    float_error = None
    
    try:
        double_result = double(val)
    except Exception as e:
        double_error = type(e).__name__
    
    try:
        float_result = float(val)
    except Exception as e:
        float_error = type(e).__name__
    
    # Check for inconsistencies
    if double_error is None and float_error is not None:
        print(f"\nBUG FOUND: double({val!r}) succeeds but float() fails with {float_error}")
        assert False
    elif double_error is not None and float_error is None:
        print(f"\nBUG FOUND: double({val!r}) fails with {double_error} but float() succeeds")
        assert False


# Test property validation edge cases
@settings(max_examples=2000, deadline=None)
@given(
    props=st.dictionaries(
        st.sampled_from(["Name", "Description", "Status", "FrameworkId", "NonExistent"]),
        st.one_of(
            st.text(),
            st.integers(),
            st.floats(),
            st.lists(st.text()),
            st.none(),
            st.booleans(),
        ),
        min_size=0,
        max_size=5
    )
)
def test_assessment_property_validation(props):
    """Test Assessment with various invalid property combinations"""
    try:
        assessment = Assessment("Test", **props)
        dict_repr = assessment.to_dict()
        
        # If it succeeded, check round-trip
        if "Properties" in dict_repr:
            assessment2 = Assessment.from_dict("Test", dict_repr["Properties"])
            assert assessment.to_dict() == assessment2.to_dict()
    except (TypeError, ValueError, AttributeError) as e:
        # Expected for invalid properties
        pass
    except Exception as e:
        # Unexpected error
        print(f"\nUnexpected error with props {props}: {e}")
        traceback.print_exc()
        assert False, f"Unexpected error: {e}"


# Test malformed nested structures
@settings(max_examples=1000, deadline=None)
@given(
    accounts=st.lists(
        st.one_of(
            st.dictionaries(
                st.sampled_from(["Id", "Name", "EmailAddress", "Invalid"]),
                st.one_of(st.text(), st.integers(), st.none()),
                min_size=0,
                max_size=4
            ),
            st.text(),  # Invalid - should be dict
            st.none(),  # Invalid
        ),
        min_size=0,
        max_size=3
    )
)
def test_scope_with_malformed_accounts(accounts):
    """Test Scope with potentially invalid account data"""
    try:
        # Filter to only valid dicts
        valid_accounts = [a for a in accounts if isinstance(a, dict)]
        if not valid_accounts:
            return
            
        account_objs = []
        for acc_data in valid_accounts:
            try:
                acc = AWSAccount(**acc_data)
                account_objs.append(acc)
            except (TypeError, ValueError):
                # Invalid account data
                pass
        
        if account_objs:
            scope = Scope(AwsAccounts=account_objs)
            dict_repr = scope.to_dict()
            
            # Try round-trip
            scope2 = Scope.from_dict(None, dict_repr)
            assert scope.to_dict() == scope2.to_dict()
    except Exception as e:
        if "unexpected keyword" in str(e):
            print(f"\nPotential bug in from_dict: {e}")


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short", "-x"])