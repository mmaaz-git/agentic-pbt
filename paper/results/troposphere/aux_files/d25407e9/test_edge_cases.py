#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import pytest
from troposphere.validators import boolean, double
from troposphere.pcaconnectorad import (
    ValidityPeriod, CertificateValidity, VpcInformation,
    Connector, Template, TemplateDefinition
)
from troposphere import AWSObject, AWSProperty

# Edge case 1: Test boolean with mixed case variations
@given(st.sampled_from(["TRUE", "FALSE", "True", "False", "TrUe", "FaLsE", "tRuE", "fAlSe"]))
def test_boolean_mixed_case(value):
    """Test that boolean validator handles mixed case strings"""
    # According to the code, only "true", "True", "false", "False" are accepted
    if value not in ["True", "False"]:
        with pytest.raises(ValueError):
            boolean(value)
    else:
        result = boolean(value)
        assert isinstance(result, bool)

# Edge case 2: Test double with special float values
def test_double_special_values():
    """Test double validator with special float values"""
    # Infinity should work
    assert double(float('inf')) == float('inf')
    assert double(float('-inf')) == float('-inf')
    
    # NaN should work
    import math
    assert math.isnan(float(double(float('nan'))))

# Edge case 3: Test double with very large numbers
@given(st.floats(min_value=1e100, max_value=1e308, allow_nan=False, allow_infinity=False))
def test_double_large_numbers(value):
    """Test double validator with very large numbers"""
    result = double(value)
    assert result == value

# Edge case 4: Test boolean with boolean-like but invalid strings
@given(st.sampled_from(["yes", "no", "on", "off", "Y", "N", "t", "f", "T", "F"]))
def test_boolean_common_invalid_strings(value):
    """Test that common boolean-like strings are rejected"""
    with pytest.raises(ValueError):
        boolean(value)

# Edge case 5: Test required properties validation
def test_required_property_missing():
    """Test that missing required properties raise appropriate errors"""
    # VpcInformation requires SecurityGroupIds
    with pytest.raises(TypeError):
        vpc = VpcInformation()

# Edge case 6: Test property type validation with wrong types
def test_wrong_property_type():
    """Test that wrong property types are caught"""
    # SecurityGroupIds should be a list of strings
    with pytest.raises(TypeError):
        vpc = VpcInformation(SecurityGroupIds="not-a-list")

# Edge case 7: Test double with integer strings
@given(st.integers())
def test_double_integer_strings(value):
    """Test that double accepts integer strings"""
    str_value = str(value)
    result = double(str_value)
    assert result == str_value

# Edge case 8: Test boolean with whitespace
@given(st.sampled_from([" true", "true ", " true ", "\ttrue", "true\n", " True ", " False "]))
def test_boolean_with_whitespace(value):
    """Test that boolean validator doesn't trim whitespace"""
    # The validator doesn't strip whitespace, so these should fail
    with pytest.raises(ValueError):
        boolean(value)

# Edge case 9: Test double with whitespace
@given(st.floats(allow_nan=False, allow_infinity=False))
def test_double_with_whitespace(value):
    """Test double validator with whitespace-padded strings"""
    str_value = f"  {value}  "
    # Python's float() does handle whitespace, so this should work
    result = double(str_value)
    assert result == str_value
    float(result)  # Should still be convertible

# Edge case 10: Test empty strings
def test_validators_empty_string():
    """Test validators with empty strings"""
    with pytest.raises(ValueError):
        boolean("")
    
    with pytest.raises(ValueError):
        double("")

# Edge case 11: Test dict properties
def test_dict_properties():
    """Test that dict properties work correctly"""
    # Tags property accepts dict
    from troposphere.pcaconnectorad import Connector
    connector = Connector(
        CertificateAuthorityArn="arn:aws:acm-pca:us-east-1:123456789012:certificate-authority/12345678",
        DirectoryId="d-1234567890",
        VpcInformation=VpcInformation(SecurityGroupIds=["sg-123"]),
        Tags={"Key": "Value", "Environment": "Test"}
    )
    assert connector.properties["Tags"] == {"Key": "Value", "Environment": "Test"}

# Edge case 12: Test ValidityPeriod with edge values
@given(st.floats(min_value=0.1, max_value=0.9, allow_nan=False))
def test_validity_period_fractional_days(period):
    """Test ValidityPeriod with fractional values"""
    vp = ValidityPeriod(Period=period, PeriodType="DAYS")
    assert vp.properties["Period"] == period

# Edge case 13: Test double with negative zero
def test_double_negative_zero():
    """Test double validator with negative zero"""
    result = double(-0.0)
    assert result == -0.0

if __name__ == "__main__":
    print("Testing edge cases...")
    test_boolean_mixed_case()
    test_double_special_values()
    print("Edge case tests completed.")