#!/usr/bin/env /root/hypothesis-llm/envs/troposphere_env/bin/python3
"""Edge case property-based tests for troposphere.chatbot module"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings, example
import pytest
from troposphere import chatbot, AWSHelperFn, Ref
from troposphere.validators.chatbot import validate_logginglevel
import json


# Test edge cases with special characters and unicode
@given(st.text())
@settings(max_examples=1000)
def test_validate_logginglevel_case_sensitivity(level):
    """
    Test case sensitivity and whitespace handling in validate_logginglevel.
    The valid values are exact matches for ERROR, INFO, NONE.
    """
    VALID_LEVELS = ("ERROR", "INFO", "NONE")
    
    # Check variations with case and whitespace
    if level.strip().upper() in VALID_LEVELS and level not in VALID_LEVELS:
        # Should fail for case variations or whitespace
        with pytest.raises(ValueError):
            validate_logginglevel(level)
    elif level in VALID_LEVELS:
        assert validate_logginglevel(level) == level


# Test with extreme values and special strings
@given(
    name=st.text() | st.just("") | st.just(None),
    arn=st.text(min_size=0, max_size=1000)
)
@settings(max_examples=500)
def test_custom_action_empty_and_special_names(name, arn):
    """
    Test CustomAction with empty, None, and special character names.
    """
    assume(name is not None)  # None would cause different error
    
    try:
        obj = chatbot.CustomAction("Action")
        obj.ActionName = name
        obj.Definition = chatbot.CustomActionDefinition(CommandText="test")
        
        # Check if validation passes
        obj._validate_props()
        
        # If we get here, the name was accepted
        assert obj.properties["ActionName"] == name
    except (ValueError, TypeError, AttributeError) as e:
        # Empty string might be rejected as required field
        if name == "":
            assert "required" in str(e).lower() or "actionname" in str(e).lower()


# Test serialization with nested objects
@given(
    button_text=st.text(min_size=0, max_size=100),
    operator=st.sampled_from(["=", "!=", ">", "<", ">=", "<=", "CONTAINS", "NOT_CONTAINS"]),
    var_name=st.text(min_size=1, max_size=50),
    value=st.text(min_size=0, max_size=100),
    notification_type=st.text(min_size=1, max_size=50),
    num_attachments=st.integers(min_value=0, max_value=10)
)
@settings(max_examples=200)
def test_custom_action_complex_attachments(button_text, operator, var_name, value, notification_type, num_attachments):
    """
    Test CustomAction with complex nested attachment structures.
    """
    attachments = []
    for i in range(num_attachments):
        criteria = chatbot.CustomActionAttachmentCriteria(
            Operator=operator,
            VariableName=f"{var_name}_{i}",
            Value=value if value else None
        )
        
        attachment = chatbot.CustomActionAttachment(
            ButtonText=button_text if button_text else None,
            Criteria=[criteria],
            NotificationType=notification_type
        )
        attachments.append(attachment)
    
    obj = chatbot.CustomAction("ComplexAction")
    obj.ActionName = "TestComplexAction"
    obj.Definition = chatbot.CustomActionDefinition(CommandText="complex command")
    if attachments:
        obj.Attachments = attachments
    
    # Test serialization
    dict_repr = obj.to_dict()
    
    # Verify structure
    assert "Properties" in dict_repr
    props = dict_repr["Properties"]
    assert props["ActionName"] == "TestComplexAction"
    if attachments:
        assert "Attachments" in props
        assert len(props["Attachments"]) == num_attachments


# Test property assignment with CloudFormation functions
@given(
    use_ref=st.booleans(),
    config_name=st.text(min_size=1, max_size=50)
)
def test_cloudformation_functions_in_properties(use_ref, config_name):
    """
    Test that CloudFormation helper functions (like Ref) work in properties.
    The code explicitly allows AWSHelperFn instances.
    """
    obj = chatbot.SlackChannelConfiguration("SlackTest")
    
    if use_ref:
        # Use CloudFormation Ref function
        obj.ConfigurationName = Ref("MyParameter")
        obj.IamRoleArn = Ref("MyRole")
        obj.SlackChannelId = Ref("MyChannel")
        obj.SlackWorkspaceId = Ref("MyWorkspace")
    else:
        obj.ConfigurationName = config_name
        obj.IamRoleArn = "arn:aws:iam::123456789012:role/test"
        obj.SlackChannelId = "C1234567890"
        obj.SlackWorkspaceId = "T1234567890"
    
    # Should be able to convert to dict even with Refs
    dict_repr = obj.to_dict()
    assert "Properties" in dict_repr


# Test boolean property coercion
@given(
    bool_value=st.sampled_from([
        True, False, 1, 0, "true", "false", "True", "False", 
        "yes", "no", "1", "0", [], [1], {}, {"a": 1}
    ])
)
def test_boolean_property_validation(bool_value):
    """
    Test UserRoleRequired boolean property with various truthy/falsy values.
    """
    obj = chatbot.MicrosoftTeamsChannelConfiguration("TeamsTest")
    obj.ConfigurationName = "test"
    obj.IamRoleArn = "arn:aws:iam::123456789012:role/test"
    obj.TeamId = "team123"
    obj.TeamsChannelId = "channel123"
    obj.TeamsTenantId = "tenant123"
    
    # The boolean validator should handle various inputs
    try:
        obj.UserRoleRequired = bool_value
        # If it succeeds, check the stored value
        stored = obj.properties.get("UserRoleRequired")
        # Should be converted to boolean
        assert isinstance(stored, bool) or isinstance(stored, AWSHelperFn)
    except (TypeError, ValueError) as e:
        # Some values might not be accepted
        # The boolean validator is strict about types
        pass


# Test with maximum field lengths
@given(
    name_length=st.integers(min_value=0, max_value=10000),
    arn_length=st.integers(min_value=0, max_value=10000)
)
@settings(max_examples=100)
def test_extreme_string_lengths(name_length, arn_length):
    """
    Test with very long strings to check for buffer overflows or limits.
    """
    long_name = "A" * name_length
    long_arn = "arn:aws:iam::123456789012:role/" + "B" * arn_length
    
    try:
        obj = chatbot.SlackChannelConfiguration("Test")
        obj.ConfigurationName = long_name
        obj.IamRoleArn = long_arn
        obj.SlackChannelId = "C" * min(name_length, 100)
        obj.SlackWorkspaceId = "T" * min(name_length, 100)
        
        # Try to serialize
        dict_repr = obj.to_dict()
        
        # Values should be preserved
        assert dict_repr["Properties"]["ConfigurationName"] == long_name
        assert dict_repr["Properties"]["IamRoleArn"] == long_arn
    except (ValueError, MemoryError, OverflowError):
        # Very long strings might cause issues
        pass


# Test round-trip with all possible fields
@given(
    config_name=st.text(min_size=1, max_size=50),
    guardrail_policies=st.lists(st.text(min_size=1, max_size=100), min_size=0, max_size=5),
    logging_level=st.sampled_from(["ERROR", "INFO", "NONE"]),
    sns_arns=st.lists(st.text(min_size=1, max_size=200), min_size=0, max_size=5),
    user_role_required=st.booleans()
)
@settings(max_examples=200)
def test_slack_full_round_trip(config_name, guardrail_policies, logging_level, sns_arns, user_role_required):
    """
    Test complete round-trip serialization with all optional fields.
    """
    # Create with all fields
    original = chatbot.SlackChannelConfiguration("FullTest")
    original.ConfigurationName = config_name
    original.IamRoleArn = "arn:aws:iam::123456789012:role/test"
    original.SlackChannelId = "C1234567890"
    original.SlackWorkspaceId = "T1234567890"
    original.GuardrailPolicies = guardrail_policies
    original.LoggingLevel = logging_level
    original.SnsTopicArns = sns_arns
    original.UserRoleRequired = user_role_required
    
    # Convert to dict
    dict_repr = original.to_dict()
    
    # Reconstruct
    props = dict_repr["Properties"]
    reconstructed = chatbot.SlackChannelConfiguration.from_dict("FullTest", props)
    
    # Compare
    assert original == reconstructed
    
    # Verify all fields
    assert reconstructed.properties["ConfigurationName"] == config_name
    assert reconstructed.properties.get("GuardrailPolicies") == guardrail_policies
    assert reconstructed.properties["LoggingLevel"] == logging_level
    assert reconstructed.properties.get("SnsTopicArns") == sns_arns
    assert reconstructed.properties["UserRoleRequired"] == user_role_required