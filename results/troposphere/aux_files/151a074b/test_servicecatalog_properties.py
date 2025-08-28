"""
Property-based tests for troposphere.servicecatalog module
"""

import math
from hypothesis import given, strategies as st, assume
import troposphere.servicecatalog as sc
import troposphere.validators


# Test 1: Boolean validator idempotence and consistency
@given(st.sampled_from([True, 1, "1", "true", "True", False, 0, "0", "false", "False"]))
def test_boolean_validator_idempotence(value):
    """The boolean validator should be idempotent - applying it twice should give the same result"""
    result1 = troposphere.validators.boolean(value)
    result2 = troposphere.validators.boolean(result1)
    assert result1 == result2
    assert isinstance(result1, bool)
    assert isinstance(result2, bool)


@given(st.sampled_from([True, 1, "1", "true", "True"]))
def test_boolean_validator_true_values(value):
    """All truthy values should return True"""
    result = troposphere.validators.boolean(value)
    assert result is True


@given(st.sampled_from([False, 0, "0", "false", "False"]))
def test_boolean_validator_false_values(value):
    """All falsy values should return False"""
    result = troposphere.validators.boolean(value)
    assert result is False


# Test 2: Integer validator properties
@given(st.integers())
def test_integer_validator_preserves_integers(value):
    """Integer validator should preserve actual integers"""
    result = troposphere.validators.integer(value)
    assert result == value
    assert type(result) == type(value)


@given(st.text())
def test_integer_validator_preserves_valid_strings(value):
    """Integer validator should preserve strings that can be converted to int"""
    try:
        int(value)
        is_valid = True
    except (ValueError, TypeError):
        is_valid = False
    
    if is_valid:
        result = troposphere.validators.integer(value)
        assert result == value
        assert type(result) == type(value)
        # The value should still be convertible after validation
        assert int(result) == int(value)


@given(st.floats(allow_nan=False, allow_infinity=False))
def test_integer_validator_with_floats(value):
    """Integer validator behavior with floats that are whole numbers"""
    if value == int(value):  # If it's a whole number
        result = troposphere.validators.integer(value)
        assert result == value
        assert int(result) == int(value)


# Test 3: validate_tag_update properties
@given(st.sampled_from(["ALLOWED", "NOT_ALLOWED"]))
def test_validate_tag_update_valid_values(value):
    """validate_tag_update should accept and return valid values unchanged"""
    result = sc.validate_tag_update(value)
    assert result == value
    assert type(result) == type(value)


@given(st.text())
def test_validate_tag_update_invalid_values(value):
    """validate_tag_update should reject invalid values"""
    if value not in ["ALLOWED", "NOT_ALLOWED"]:
        try:
            sc.validate_tag_update(value)
            assert False, f"Should have raised ValueError for {value}"
        except ValueError as e:
            assert "is not a valid tag update value" in str(e)


# Test 4: Round-trip property for ResourceUpdateConstraint
@given(st.sampled_from(["ALLOWED", "NOT_ALLOWED"]))
def test_resource_update_constraint_roundtrip(tag_value):
    """ResourceUpdateConstraint should preserve valid tag update values in to_dict()"""
    constraint = sc.ResourceUpdateConstraint(
        'TestConstraint',
        PortfolioId='portfolio-123',
        ProductId='product-456',
        TagUpdateOnProvisionedProduct=tag_value
    )
    result_dict = constraint.to_dict()
    assert result_dict['Properties']['TagUpdateOnProvisionedProduct'] == tag_value


# Test 5: CloudFormationProduct boolean property handling
@given(st.sampled_from([True, 1, "1", "true", "True", False, 0, "0", "false", "False"]))
def test_cloudformation_product_boolean_handling(bool_value):
    """CloudFormationProduct should handle various boolean representations consistently"""
    product = sc.CloudFormationProduct(
        'TestProduct',
        Name='MyProduct',
        Owner='MyOwner',
        ReplaceProvisioningArtifacts=bool_value
    )
    result_dict = product.to_dict()
    # The boolean validator should normalize to actual boolean
    prop_value = result_dict['Properties'].get('ReplaceProvisioningArtifacts')
    if prop_value is not None:
        assert isinstance(prop_value, bool)
        # Check it matches expected boolean value
        if bool_value in [True, 1, "1", "true", "True"]:
            assert prop_value is True
        else:
            assert prop_value is False


# Test 6: Integer validator edge cases
@given(st.sampled_from(["0", "-0", "+0", "00", "000"]))
def test_integer_validator_zero_representations(value):
    """Integer validator should handle different representations of zero"""
    result = troposphere.validators.integer(value)
    assert result == value
    assert int(result) == 0


@given(st.text(min_size=1))
def test_integer_validator_whitespace_handling(value):
    """Test how integer validator handles strings with whitespace"""
    # Add whitespace
    value_with_space = f" {value} "
    
    # Check if the trimmed value is a valid integer
    try:
        int(value.strip())
        trimmed_is_valid = True
    except (ValueError, TypeError):
        trimmed_is_valid = False
    
    # The validator should handle consistently
    try:
        result = troposphere.validators.integer(value_with_space)
        # If it succeeds, the original must have been convertible
        assert int(value_with_space) == int(result)
    except ValueError:
        # If it fails, it should be because the value isn't convertible
        try:
            int(value_with_space)
            assert False, "Should have been convertible if int() works"
        except (ValueError, TypeError):
            pass  # Expected