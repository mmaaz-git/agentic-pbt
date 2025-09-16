#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import pytest
from troposphere.validators import boolean, double
from troposphere.pcaconnectorad import (
    ValidityPeriod, CertificateValidity, EnrollmentFlagsV2,
    PrivateKeyAttributesV2, VpcInformation, Connector
)

# Test 1: Boolean validator identity property
@given(st.sampled_from([True, False, 1, 0, "true", "false", "True", "False", "1", "0"]))
def test_boolean_validator_idempotence(value):
    """Test that applying boolean twice gives the same result as applying once"""
    result1 = boolean(value)
    result2 = boolean(result1)
    assert result1 == result2

# Test 2: Boolean validator conversion consistency
@given(st.sampled_from([(True, 1, "1", "true", "True"), (False, 0, "0", "false", "False")]))
def test_boolean_validator_equivalence(equiv_values):
    """Test that equivalent boolean representations produce the same result"""
    results = [boolean(v) for v in equiv_values]
    assert len(set(results)) == 1  # All should produce the same result

# Test 3: Boolean validator invalid input
@given(st.text().filter(lambda x: x not in ["true", "false", "True", "False", "1", "0"]))
def test_boolean_validator_invalid_raises(value):
    """Test that invalid inputs raise ValueError"""
    assume(value not in ["", " "])  # Skip empty strings as they might be edge cases
    with pytest.raises(ValueError):
        boolean(value)

# Test 4: Double validator accepts valid numeric inputs
@given(st.one_of(
    st.floats(allow_nan=False, allow_infinity=False),
    st.integers(),
))
def test_double_validator_accepts_numbers(value):
    """Test that double validator accepts valid numeric values"""
    result = double(value)
    assert result == value

# Test 5: Double validator accepts string representations of numbers
@given(st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10))
def test_double_validator_string_conversion(value):
    """Test that double validator accepts string representations of numbers"""
    str_value = str(value)
    result = double(str_value)
    assert result == str_value
    # Verify it's a valid number by trying to convert
    float(result)

# Test 6: Double validator rejects non-numeric strings
@given(st.text().filter(lambda x: not x.replace('.', '').replace('-', '').replace('+', '').replace('e', '').isdigit()))
def test_double_validator_invalid_raises(value):
    """Test that non-numeric strings raise ValueError"""
    assume(value)  # Skip empty strings
    assume(not value.strip().replace('.', '').replace('-', '').replace('+', '').replace('e', '').replace('E', '').isdigit())
    try:
        float(value)
        # If float() succeeds, skip this test case
        assume(False)
    except (ValueError, TypeError):
        # This is what we expect - now test our validator
        with pytest.raises(ValueError):
            double(value)

# Test 7: ValidityPeriod requires Period and PeriodType
@given(
    st.floats(min_value=1, max_value=365, allow_nan=False),
    st.sampled_from(["DAYS", "MONTHS", "YEARS"])
)
def test_validity_period_creation(period, period_type):
    """Test that ValidityPeriod can be created with valid inputs"""
    vp = ValidityPeriod(Period=period, PeriodType=period_type)
    assert vp.properties["Period"] == period
    assert vp.properties["PeriodType"] == period_type

# Test 8: CertificateValidity requires both renewal and validity periods
@given(
    st.floats(min_value=1, max_value=365, allow_nan=False),
    st.floats(min_value=1, max_value=365, allow_nan=False),
    st.sampled_from(["DAYS", "MONTHS", "YEARS"]),
    st.sampled_from(["DAYS", "MONTHS", "YEARS"])
)
def test_certificate_validity_creation(renewal_period, validity_period, renewal_type, validity_type):
    """Test that CertificateValidity correctly stores nested ValidityPeriod objects"""
    renewal = ValidityPeriod(Period=renewal_period, PeriodType=renewal_type)
    validity = ValidityPeriod(Period=validity_period, PeriodType=validity_type)
    cert_validity = CertificateValidity(RenewalPeriod=renewal, ValidityPeriod=validity)
    
    assert cert_validity.properties["RenewalPeriod"] == renewal
    assert cert_validity.properties["ValidityPeriod"] == validity

# Test 9: EnrollmentFlagsV2 boolean properties
@given(
    st.booleans(),
    st.booleans(),
    st.booleans(),
    st.booleans(),
    st.booleans()
)
def test_enrollment_flags_v2_boolean_properties(flag1, flag2, flag3, flag4, flag5):
    """Test that EnrollmentFlagsV2 correctly handles boolean properties"""
    flags = EnrollmentFlagsV2(
        EnableKeyReuseOnNtTokenKeysetStorageFull=flag1,
        IncludeSymmetricAlgorithms=flag2,
        NoSecurityExtension=flag3,
        RemoveInvalidCertificateFromPersonalStore=flag4,
        UserInteractionRequired=flag5
    )
    
    # The boolean validator should be applied
    assert flags.properties.get("EnableKeyReuseOnNtTokenKeysetStorageFull") == flag1
    assert flags.properties.get("IncludeSymmetricAlgorithms") == flag2
    assert flags.properties.get("NoSecurityExtension") == flag3
    assert flags.properties.get("RemoveInvalidCertificateFromPersonalStore") == flag4
    assert flags.properties.get("UserInteractionRequired") == flag5

# Test 10: PrivateKeyAttributesV2 MinimalKeyLength validation
@given(st.floats(min_value=512, max_value=16384, allow_nan=False))
def test_private_key_attributes_minimal_key_length(key_length):
    """Test that PrivateKeyAttributesV2 accepts numeric key lengths"""
    pka = PrivateKeyAttributesV2(
        KeySpec="RSA",
        MinimalKeyLength=key_length
    )
    assert pka.properties["MinimalKeyLength"] == key_length

# Test 11: Type checking for boolean validator on numeric-like strings
@given(st.sampled_from(["2", "3", "-1", "100", "true1", "1true", "false0", "0false"]))
def test_boolean_validator_numeric_edge_cases(value):
    """Test that numeric-like strings that aren't exactly "1" or "0" raise ValueError"""
    with pytest.raises(ValueError):
        boolean(value)

# Test 12: Testing validator edge case - None input
def test_validators_none_input():
    """Test that validators handle None input appropriately"""
    with pytest.raises(ValueError):
        boolean(None)
    
    with pytest.raises(ValueError):
        double(None)

# Test 13: Double validator with exponential notation
@given(st.sampled_from(["1e10", "2.5e-5", "1E3", "-3.14e2"]))
def test_double_validator_exponential_notation(value):
    """Test that double validator accepts exponential notation"""
    result = double(value)
    assert result == value
    # Verify it's valid by converting
    float(result)

if __name__ == "__main__":
    # Run a quick test to ensure imports work
    print("Running property-based tests for troposphere.pcaconnectorad...")
    test_boolean_validator_idempotence()
    test_boolean_validator_equivalence()
    print("Basic tests passed. Run with pytest for full test suite.")