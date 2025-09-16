"""
Property-based tests for troposphere.signer module
"""

import math
from hypothesis import given, assume, strategies as st
import troposphere.signer as signer


# Test 1: integer function should only accept values that are actually integers
@given(st.floats(allow_nan=False, allow_infinity=False))
def test_integer_function_rejects_non_integers(x):
    """The integer function should accept a value if and only if it represents an integer."""
    
    try:
        result = signer.integer(x)
        # If it accepts the value, the value should be convertible to int without loss
        int_val = int(result)
        
        # The original value should be exactly equal to its integer representation
        # This fails for values like 42.5 which the function incorrectly accepts
        if isinstance(x, float):
            assert x == float(int_val), f"integer() accepted non-integer float {x}"
            
    except (ValueError, TypeError):
        # If it rejects the value, it should not be a valid integer
        if isinstance(x, (int, float)):
            # Floats that are exactly integers should be accepted
            assert x != float(int(x)), f"integer() rejected valid integer {x}"


# Test 2: Round-trip property for SignatureValidityPeriod
@given(
    st.dictionaries(
        st.sampled_from(['Type', 'Value']),
        st.one_of(
            st.text(min_size=1, max_size=20),
            st.integers(min_value=-1000, max_value=1000)
        ),
        min_size=0,
        max_size=2
    )
)
def test_signature_validity_period_roundtrip(data):
    """to_dict(from_dict(x)) should equal x for valid inputs"""
    
    # Filter out invalid Value entries
    if 'Value' in data:
        # The Value field uses the integer validator, so it should be int-convertible
        try:
            int(data['Value'])
        except (ValueError, TypeError):
            assume(False)  # Skip this test case
    
    # Create from dict
    svp = signer.SignatureValidityPeriod.from_dict('TestSVP', data)
    
    # Convert back to dict
    result = svp.to_dict()
    
    # They should be equal
    assert data == result, f"Round-trip failed: {data} != {result}"


# Test 3: SignatureValidityPeriod with validation disabled
@given(st.floats(allow_nan=False, allow_infinity=False))
def test_signature_validity_period_no_validation(value):
    """With validation disabled, to_dict should still handle Value correctly"""
    
    svp = signer.SignatureValidityPeriod(Type='Days', Value=value)
    
    # With validation=False, it should not validate but still process
    try:
        result_no_val = svp.to_dict(validation=False)
        # If it succeeds without validation, with validation should also work
        # for valid integers
        result_with_val = svp.to_dict(validation=True)
        
        # Both should give same result for valid values
        assert result_no_val == result_with_val
        
    except (ValueError, TypeError) as e:
        # If validation=False fails, it's a processing error not validation
        if "is not a valid integer" not in str(e):
            raise


# Test 4: SigningProfile properties
@given(
    platform_id=st.text(min_size=1, max_size=50),
    days=st.integers(min_value=1, max_value=3650)
)
def test_signing_profile_creation(platform_id, days):
    """SigningProfile should correctly handle SignatureValidityPeriod"""
    
    svp = signer.SignatureValidityPeriod(Type='Days', Value=days)
    profile = signer.SigningProfile(
        'TestProfile',
        PlatformId=platform_id,
        SignatureValidityPeriod=svp
    )
    
    result = profile.to_dict()
    
    assert result['PlatformId'] == platform_id
    assert 'SignatureValidityPeriod' in result
    assert result['SignatureValidityPeriod']['Value'] == days


# Test 5: ProfilePermission required fields
@given(
    action=st.text(min_size=1, max_size=50),
    principal=st.text(min_size=1, max_size=50),
    profile_name=st.text(min_size=1, max_size=50),
    statement_id=st.text(min_size=1, max_size=50)
)
def test_profile_permission_required_fields(action, principal, profile_name, statement_id):
    """ProfilePermission should handle all required fields correctly"""
    
    perm = signer.ProfilePermission(
        'TestPermission',
        Action=action,
        Principal=principal,
        ProfileName=profile_name,
        StatementId=statement_id
    )
    
    result = perm.to_dict()
    
    # All required fields should be present
    assert result['Action'] == action
    assert result['Principal'] == principal
    assert result['ProfileName'] == profile_name
    assert result['StatementId'] == statement_id