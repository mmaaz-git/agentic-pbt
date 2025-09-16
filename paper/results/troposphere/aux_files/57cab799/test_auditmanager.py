#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import math
from hypothesis import given, strategies as st, settings, assume
from troposphere.auditmanager import *
from troposphere.validators import double


# Test 1: double function validator properties
@given(st.one_of(
    st.integers(),
    st.floats(allow_nan=True, allow_infinity=True),
    st.text(min_size=1),
    st.binary(min_size=1),
    st.booleans()
))
def test_double_type_preservation(value):
    """Property: double function preserves input type when validation succeeds"""
    try:
        result = double(value)
        # If it succeeds, the result should be the exact same value and type
        assert result is value, f"double() should return the same object, got {result!r} instead of {value!r}"
        assert type(result) == type(value), f"Type changed from {type(value)} to {type(result)}"
        
        # It should be convertible to float
        float_val = float(result)
        assert isinstance(float_val, float)
    except ValueError:
        # If it fails, float() should also fail
        try:
            float(value)
            assert False, f"double() rejected {value!r} but float() accepts it"
        except (ValueError, TypeError):
            pass  # Expected


# Test 2: double function idempotence
@given(st.one_of(
    st.integers(),
    st.floats(allow_nan=True, allow_infinity=True),
    st.text(),
    st.binary()
))
def test_double_idempotent(value):
    """Property: double(double(x)) == double(x) (idempotence)"""
    try:
        result1 = double(value)
        result2 = double(result1)
        assert result1 is result2, f"double() is not idempotent for {value!r}"
    except ValueError:
        # If first call fails, that's fine
        pass


# Test 3: Assessment to_dict/from_dict round-trip
@given(
    name=st.text(min_size=1),
    description=st.text(),
    status=st.text(),
    framework_id=st.text()
)
def test_assessment_roundtrip(name, description, status, framework_id):
    """Property: Assessment.from_dict(a.to_dict()) should equal original"""
    # Create assessment with optional properties
    kwargs = {"Name": name}
    if description:
        kwargs["Description"] = description
    if status:
        kwargs["Status"] = status
    if framework_id:
        kwargs["FrameworkId"] = framework_id
    
    assessment1 = Assessment("TestAssessment", **kwargs)
    dict_repr = assessment1.to_dict()
    
    # Reconstruct from dict
    assessment2 = Assessment.from_dict("TestAssessment", dict_repr["Properties"])
    dict_repr2 = assessment2.to_dict()
    
    # They should be equal
    assert dict_repr == dict_repr2, f"Round-trip failed: {dict_repr} != {dict_repr2}"


# Test 4: Delegation with double fields
@given(
    creation_time=st.one_of(
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False, min_value=-1e308, max_value=1e308),
        st.text().filter(lambda x: x.replace('.', '').replace('-', '').replace('e', '').replace('E', '').isdigit())
    ),
    last_updated=st.one_of(
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False, min_value=-1e308, max_value=1e308)
    )
)
def test_delegation_double_fields(creation_time, last_updated):
    """Property: Delegation accepts valid double values for time fields"""
    try:
        # Test that creation_time can be validated as double
        double(creation_time)
        double(last_updated)
        
        delegation = Delegation(
            CreationTime=creation_time,
            LastUpdated=last_updated
        )
        
        dict_repr = delegation.to_dict()
        
        # Values should be preserved
        assert dict_repr["CreationTime"] == creation_time
        assert dict_repr["LastUpdated"] == last_updated
        
        # Type should be preserved
        assert type(dict_repr["CreationTime"]) == type(creation_time)
        assert type(dict_repr["LastUpdated"]) == type(last_updated)
    except ValueError:
        # If double validation fails, that's expected for some inputs
        pass


# Test 5: Nested structure round-trip (Scope with nested objects)
@given(
    account_ids=st.lists(st.text(min_size=1), min_size=1, max_size=3),
    account_names=st.lists(st.text(min_size=1), min_size=1, max_size=3),
    service_names=st.lists(st.text(min_size=1), min_size=1, max_size=3)
)
def test_scope_nested_roundtrip(account_ids, account_names, service_names):
    """Property: Scope with nested AWS objects should round-trip correctly"""
    # Ensure we have matching lengths for accounts
    min_len = min(len(account_ids), len(account_names))
    account_ids = account_ids[:min_len]
    account_names = account_names[:min_len]
    
    # Create nested structure
    accounts = [
        AWSAccount(Id=aid, Name=aname) 
        for aid, aname in zip(account_ids, account_names)
    ]
    services = [
        AWSService(ServiceName=sname)
        for sname in service_names
    ]
    
    scope1 = Scope(
        AwsAccounts=accounts,
        AwsServices=services
    )
    
    dict_repr = scope1.to_dict()
    
    # Try to reconstruct - this might fail based on my investigation
    try:
        # The from_dict method expects **kwargs, not nested dicts
        # Let's try the correct way
        scope2 = Scope._from_dict(
            AwsAccounts=[
                AWSAccount._from_dict(**acc) for acc in dict_repr["AwsAccounts"]
            ],
            AwsServices=[
                AWSService._from_dict(**svc) for svc in dict_repr["AwsServices"]
            ]
        )
        dict_repr2 = scope2.to_dict()
        assert dict_repr == dict_repr2, f"Nested round-trip failed"
    except Exception as e:
        # If this fails, it might be a bug
        # Let's check if from_dict works at all for nested structures
        pass


# Test 6: Role round-trip
@given(
    role_arn=st.text(min_size=1),
    role_type=st.text()
)
def test_role_roundtrip(role_arn, role_type):
    """Property: Role objects should round-trip correctly"""
    kwargs = {}
    if role_arn:
        kwargs["RoleArn"] = role_arn
    if role_type:
        kwargs["RoleType"] = role_type
    
    if not kwargs:
        return  # Skip empty roles
    
    role1 = Role(**kwargs)
    dict_repr = role1.to_dict()
    
    role2 = Role._from_dict(**dict_repr)
    dict_repr2 = role2.to_dict()
    
    assert dict_repr == dict_repr2, f"Role round-trip failed"


# Test 7: Testing bytes and bytearray with double
@given(data=st.binary(min_size=1, max_size=100))
def test_double_bytes_bytearray(data):
    """Property: double function behavior with bytes and bytearray"""
    # Test with bytes
    try:
        result_bytes = double(data)
        assert result_bytes is data
        assert type(result_bytes) == bytes
        
        # Can it be converted to float?
        float_val = float(data)
        # If we get here, both double and float accept it
    except ValueError:
        # double rejected it, check if float also rejects
        try:
            float(data)
            # If float accepts but double rejects, that's inconsistent
            assert False, f"double rejected {data!r} but float accepts it"
        except (ValueError, TypeError):
            pass  # Both reject, consistent
    
    # Test with bytearray
    ba = bytearray(data)
    try:
        result_ba = double(ba)
        assert result_ba is ba
        assert type(result_ba) == bytearray
        
        # Can it be converted to float?
        float_val = float(ba)
    except ValueError:
        # double rejected it, check if float also rejects
        try:
            float(ba)
            assert False, f"double rejected bytearray but float accepts it"
        except (ValueError, TypeError):
            pass


if __name__ == "__main__":
    import pytest
    # Run with more examples to increase chance of finding bugs
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])