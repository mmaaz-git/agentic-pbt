"""
Additional property-based tests to find edge cases
"""

from hypothesis import given, strategies as st, settings
import troposphere.servicecatalog as sc
import troposphere.validators


# Test boolean validator with unexpected types
@given(st.one_of(
    st.lists(st.booleans()),
    st.dictionaries(st.text(), st.booleans()),
    st.none(),
    st.binary(),
    st.complex_numbers()
))
def test_boolean_validator_unexpected_types(value):
    """Boolean validator should raise ValueError for unexpected types"""
    try:
        result = troposphere.validators.boolean(value)
        # If it succeeds, it should be one of the valid values
        assert False, f"Should have raised ValueError for {type(value)}: {value}"
    except ValueError:
        pass  # Expected


# Test case sensitivity edge cases
@given(st.sampled_from(["TRUE", "FALSE", "True", "False", "TrUe", "FaLsE"]))
def test_boolean_validator_case_variations(value):
    """Test case sensitivity in boolean validator"""
    try:
        result = troposphere.validators.boolean(value)
        # Only "True" and "False" (exact case) should work
        assert value in ["True", "False"]
        if value == "True":
            assert result is True
        else:
            assert result is False
    except ValueError:
        # Other case variations should fail
        assert value not in ["True", "False"]


# Test integer validator with string representations of floats
@given(st.floats(allow_nan=False, allow_infinity=False).map(str))
def test_integer_validator_float_strings(value):
    """Integer validator with string representations of floats"""
    try:
        result = troposphere.validators.integer(value)
        # If it succeeds, the string must be convertible to int
        int_value = int(float(value))
        assert result == value
    except ValueError:
        # Should fail for non-integer float strings
        try:
            int(value)
            assert False, f"Should have failed but int({value}) worked"
        except (ValueError, TypeError):
            pass  # Expected


# Test integer validator with special number formats
@given(st.sampled_from(["0x10", "0o10", "0b10", "1e10", "1E10", "1.0e10"]))
def test_integer_validator_special_formats(value):
    """Integer validator with special number formats"""
    try:
        result = troposphere.validators.integer(value)
        # Check if Python's int() can handle it
        int_value = int(value, 0) if value.startswith(("0x", "0o", "0b")) else int(value)
        assert result == value
    except ValueError:
        # Some formats might not be accepted
        pass


# Test boolean validator preserves type strictly
@given(st.sampled_from([True, 1, "1", "true", "True"]))
def test_boolean_return_type_consistency(value):
    """Boolean validator should always return bool type, not the input type"""
    result = troposphere.validators.boolean(value)
    assert type(result) == bool
    assert result is True


# Test with very long strings
@given(st.text(min_size=1000, max_size=10000))
def test_validate_tag_update_long_strings(value):
    """validate_tag_update should handle very long strings gracefully"""
    if value not in ["ALLOWED", "NOT_ALLOWED"]:
        try:
            sc.validate_tag_update(value)
            assert False, "Should have raised ValueError"
        except ValueError as e:
            # The error message should still be reasonable
            assert "is not a valid tag update value" in str(e)


# Test validate_tag_update with close matches
@given(st.sampled_from(["ALLOWED ", " ALLOWED", "allowed", "ALLOW", "NOT_ALLOW", "NOT ALLOWED"]))
def test_validate_tag_update_close_matches(value):
    """validate_tag_update should be strict about exact matches"""
    try:
        result = sc.validate_tag_update(value)
        # Should only succeed for exact matches
        assert False, f"Should have rejected '{value}'"
    except ValueError as e:
        assert "is not a valid tag update value" in str(e)


# Test integer edge cases with large numbers
@given(st.integers(min_value=10**100, max_value=10**200))
def test_integer_validator_very_large_numbers(value):
    """Integer validator should handle very large integers"""
    result = troposphere.validators.integer(value)
    assert result == value
    assert int(result) == value


# Test integer validator with numeric strings containing underscores
@given(st.sampled_from(["1_000", "1_000_000", "123_456_789"]))
def test_integer_validator_underscore_numbers(value):
    """Test integer validator with Python's numeric underscore syntax"""
    try:
        result = troposphere.validators.integer(value)
        # Python 3.6+ supports underscores in numeric literals
        assert int(value) == int(value.replace("_", ""))
        assert result == value
    except ValueError:
        # Might not be supported
        pass


# Test CloudFormationProduct with mixed property types
@given(
    st.sampled_from([True, False, 1, 0, "true", "false"]),
    st.text(min_size=1, max_size=100)
)
@settings(max_examples=50)
def test_cloudformation_product_mixed_properties(bool_val, name_val):
    """Test CloudFormationProduct handles mixed property types correctly"""
    try:
        product = sc.CloudFormationProduct(
            'TestProduct',
            Name=name_val,
            Owner='TestOwner',
            ReplaceProvisioningArtifacts=bool_val
        )
        result = product.to_dict()
        
        # Name should be preserved as string
        assert result['Properties']['Name'] == name_val
        
        # Boolean should be normalized
        if 'ReplaceProvisioningArtifacts' in result['Properties']:
            assert isinstance(result['Properties']['ReplaceProvisioningArtifacts'], bool)
    except Exception as e:
        # Some bool values might not be valid
        if bool_val not in [True, False, 1, 0, "1", "0", "true", "false", "True", "False"]:
            pass  # Expected to fail
        else:
            raise  # Unexpected failure