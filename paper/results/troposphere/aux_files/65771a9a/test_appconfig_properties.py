"""Property-based tests for troposphere.appconfig validators"""

import re
from hypothesis import given, strategies as st, assume
from troposphere.validators.appconfig import (
    validate_growth_type,
    validate_replicate_to,
    validate_validator_type,
)


# Property 1: Identity property - valid inputs returned unchanged
@given(st.sampled_from(["LINEAR"]))
def test_growth_type_identity(value):
    """Valid growth types should be returned unchanged"""
    assert validate_growth_type(value) == value


@given(st.sampled_from(["NONE", "SSM_DOCUMENT"]))
def test_replicate_to_identity(value):
    """Valid replication destinations should be returned unchanged"""
    assert validate_replicate_to(value) == value


@given(st.sampled_from(["JSON_SCHEMA", "LAMBDA"]))
def test_validator_type_identity(value):
    """Valid validator types should be returned unchanged"""
    assert validate_validator_type(value) == value


# Property 2: Invalid inputs should raise ValueError with consistent message
@given(st.text(min_size=1))
def test_growth_type_invalid(value):
    """Invalid growth types should raise ValueError with correct message"""
    assume(value not in ["LINEAR"])
    try:
        validate_growth_type(value)
        assert False, f"Should have raised ValueError for {value}"
    except ValueError as e:
        msg = str(e)
        assert "DeploymentStrategy GrowthType must be one of:" in msg
        assert "LINEAR" in msg


@given(st.text(min_size=1))
def test_replicate_to_invalid(value):
    """Invalid replication destinations should raise ValueError with correct message"""
    assume(value not in ["NONE", "SSM_DOCUMENT"])
    try:
        validate_replicate_to(value)
        assert False, f"Should have raised ValueError for {value}"
    except ValueError as e:
        msg = str(e)
        assert "DeploymentStrategy ReplicateTo must be one of:" in msg
        assert "NONE" in msg
        assert "SSM_DOCUMENT" in msg


@given(st.text(min_size=1))
def test_validator_type_invalid(value):
    """Invalid validator types should raise ValueError with correct message"""
    assume(value not in ["JSON_SCHEMA", "LAMBDA"])
    try:
        validate_validator_type(value)
        assert False, f"Should have raised ValueError for {value}"
    except ValueError as e:
        msg = str(e)
        assert "ConfigurationProfile Validator Type must be one of:" in msg
        assert "JSON_SCHEMA" in msg
        assert "LAMBDA" in msg


# Property 3: Case sensitivity - lowercase versions should fail
@given(st.sampled_from(["linear", "Linear", "LINEAR"]))
def test_growth_type_case_sensitivity(value):
    """Only uppercase LINEAR should be valid"""
    if value == "LINEAR":
        assert validate_growth_type(value) == value
    else:
        try:
            validate_growth_type(value)
            assert False, f"Should have raised ValueError for {value}"
        except ValueError:
            pass  # Expected


@given(st.sampled_from(["none", "ssm_document", "None", "Ssm_Document", "NONE", "SSM_DOCUMENT"]))
def test_replicate_to_case_sensitivity(value):
    """Only uppercase NONE and SSM_DOCUMENT should be valid"""
    if value in ["NONE", "SSM_DOCUMENT"]:
        assert validate_replicate_to(value) == value
    else:
        try:
            validate_replicate_to(value)
            assert False, f"Should have raised ValueError for {value}"
        except ValueError:
            pass  # Expected


# Property 4: Error message formatting - check if join produces correct format
def test_error_message_format_growth_type():
    """Test that error message has proper formatting for growth type"""
    try:
        validate_growth_type("INVALID")
    except ValueError as e:
        msg = str(e)
        # Check that the message matches expected format
        assert msg == "DeploymentStrategy GrowthType must be one of: LINEAR"


def test_error_message_format_replicate_to():
    """Test that error message has proper formatting for replicate_to"""
    try:
        validate_replicate_to("INVALID")
    except ValueError as e:
        msg = str(e)
        # Check that the message matches expected format
        # The order should be NONE, SSM_DOCUMENT based on the tuple definition
        assert msg == "DeploymentStrategy ReplicateTo must be one of: NONE, SSM_DOCUMENT"


def test_error_message_format_validator_type():
    """Test that error message has proper formatting for validator type"""
    try:
        validate_validator_type("INVALID")
    except ValueError as e:
        msg = str(e)
        # Check that the message matches expected format
        assert msg == "ConfigurationProfile Validator Type must be one of: JSON_SCHEMA, LAMBDA"


# Property 5: Test with special characters and edge cases
@given(st.one_of(
    st.text(alphabet="!@#$%^&*()[]{}|\\:;\"'<>,.?/", min_size=1),
    st.sampled_from(["", " ", "\n", "\t", "None", "null", "undefined"])
))
def test_special_characters_growth_type(value):
    """Special characters and edge cases should be rejected"""
    if value != "LINEAR":
        try:
            validate_growth_type(value)
            assert False, f"Should have raised ValueError for {repr(value)}"
        except ValueError as e:
            assert "DeploymentStrategy GrowthType must be one of:" in str(e)


# Property 6: Empty string handling
def test_empty_string_validators():
    """Empty strings should be rejected by all validators"""
    validators = [
        (validate_growth_type, "DeploymentStrategy GrowthType"),
        (validate_replicate_to, "DeploymentStrategy ReplicateTo"),
        (validate_validator_type, "ConfigurationProfile Validator Type"),
    ]
    
    for validator, name_prefix in validators:
        try:
            validator("")
            assert False, f"{validator.__name__} should reject empty string"
        except ValueError as e:
            assert name_prefix in str(e)


# Property 7: None value handling
def test_none_value_validators():
    """None values should be rejected or cause TypeError"""
    validators = [validate_growth_type, validate_replicate_to, validate_validator_type]
    
    for validator in validators:
        try:
            result = validator(None)
            # If it doesn't raise an error, None should not be in valid values
            assert False, f"{validator.__name__} accepted None value"
        except (ValueError, TypeError):
            pass  # Expected - either ValueError or TypeError is acceptable