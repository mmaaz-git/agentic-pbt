#!/usr/bin/env /root/hypothesis-llm/envs/troposphere_env/bin/python3
"""Property-based tests for troposphere.chatbot module"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import pytest
from troposphere import chatbot
from troposphere.validators.chatbot import validate_logginglevel


# Test 1: validate_logginglevel validator invariant
@given(st.text())
def test_validate_logginglevel_invariant(level):
    """
    Test that validate_logginglevel only accepts ERROR, INFO, or NONE.
    This is explicitly claimed in the validator function.
    """
    VALID_LEVELS = ("ERROR", "INFO", "NONE")
    
    if level in VALID_LEVELS:
        # Should succeed for valid levels
        result = validate_logginglevel(level)
        assert result == level
    else:
        # Should raise ValueError for invalid levels
        with pytest.raises(ValueError) as exc_info:
            validate_logginglevel(level)
        assert "LoggingLevel must be one of: ERROR, INFO, NONE" in str(exc_info.value)


# Test 2: Required field validation
@given(
    config_name=st.text(min_size=1),
    team_id=st.text(min_size=1),
    channel_id=st.text(min_size=1),
    tenant_id=st.text(min_size=1),
    iam_role=st.text(min_size=1),
    include_optional=st.booleans()
)
def test_microsoft_teams_required_fields(config_name, team_id, channel_id, tenant_id, iam_role, include_optional):
    """
    Test that MicrosoftTeamsChannelConfiguration validates required fields.
    According to the props dict, these fields are required:
    - ConfigurationName
    - IamRoleArn  
    - TeamId
    - TeamsChannelId
    - TeamsTenantId
    """
    kwargs = {
        "ConfigurationName": config_name,
        "IamRoleArn": iam_role,
        "TeamId": team_id,
        "TeamsChannelId": channel_id,
        "TeamsTenantId": tenant_id
    }
    
    if include_optional:
        kwargs["LoggingLevel"] = "INFO"
        kwargs["UserRoleRequired"] = True
    
    # Should successfully create object with all required fields
    obj = chatbot.MicrosoftTeamsChannelConfiguration("TestConfig", **kwargs)
    
    # Validation should pass
    obj._validate_props()
    
    # All required fields should be present in properties
    assert obj.properties["ConfigurationName"] == config_name
    assert obj.properties["IamRoleArn"] == iam_role
    assert obj.properties["TeamId"] == team_id
    assert obj.properties["TeamsChannelId"] == channel_id
    assert obj.properties["TeamsTenantId"] == tenant_id


@given(
    config_name=st.text(min_size=1),
    slack_channel=st.text(min_size=1),
    slack_workspace=st.text(min_size=1),
    iam_role=st.text(min_size=1)
)
def test_slack_missing_required_field_raises(config_name, slack_channel, slack_workspace, iam_role):
    """
    Test that SlackChannelConfiguration raises error when required field is missing.
    """
    # Create object missing a required field (SlackWorkspaceId)
    obj = chatbot.SlackChannelConfiguration("TestSlack")
    obj.ConfigurationName = config_name
    obj.IamRoleArn = iam_role
    obj.SlackChannelId = slack_channel
    # Intentionally not setting SlackWorkspaceId
    
    # Validation should fail for missing required field
    with pytest.raises(ValueError) as exc_info:
        obj._validate_props()
    assert "SlackWorkspaceId required" in str(exc_info.value)


# Test 3: Round-trip serialization property
@given(
    action_name=st.text(min_size=1, max_size=50),
    command_text=st.text(min_size=1, max_size=100),
    alias_name=st.text(min_size=0, max_size=50) | st.none()
)
def test_custom_action_round_trip(action_name, command_text, alias_name):
    """
    Test that CustomAction can be serialized to dict and reconstructed.
    Round-trip property: from_dict(to_dict(obj)) should equal original.
    """
    # Create original object
    kwargs = {
        "ActionName": action_name,
        "Definition": chatbot.CustomActionDefinition(CommandText=command_text)
    }
    if alias_name:
        kwargs["AliasName"] = alias_name
    
    original = chatbot.CustomAction("TestAction", **kwargs)
    
    # Serialize to dict
    dict_repr = original.to_dict()
    
    # Reconstruct from dict
    properties = dict_repr.get("Properties", {})
    reconstructed = chatbot.CustomAction.from_dict("TestAction", properties)
    
    # Should be equal
    assert original == reconstructed
    assert original.properties["ActionName"] == reconstructed.properties["ActionName"]
    

# Test 4: Type validation
@given(
    invalid_logging_level=st.integers() | st.floats() | st.lists(st.text())
)
def test_slack_logging_level_type_validation(invalid_logging_level):
    """
    Test that SlackChannelConfiguration validates LoggingLevel type.
    LoggingLevel uses validate_logginglevel function validator.
    """
    assume(not isinstance(invalid_logging_level, str))
    
    obj = chatbot.SlackChannelConfiguration("TestSlack")
    obj.ConfigurationName = "test"
    obj.IamRoleArn = "arn:aws:iam::123456789012:role/test"
    obj.SlackChannelId = "C1234567890"
    obj.SlackWorkspaceId = "T1234567890"
    
    # Setting invalid type for LoggingLevel should raise error
    with pytest.raises((TypeError, ValueError, AttributeError)):
        obj.LoggingLevel = invalid_logging_level


# Test 5: List property validation
@given(
    policies=st.lists(st.text(min_size=1), min_size=0, max_size=5),
    sns_arns=st.lists(st.text(min_size=1), min_size=0, max_size=5),
    invalid_value=st.text() | st.integers()
)
def test_list_property_validation(policies, sns_arns, invalid_value):
    """
    Test that list properties only accept lists.
    GuardrailPolicies and SnsTopicArns are defined as [str] in props.
    """
    obj = chatbot.SlackChannelConfiguration("TestSlack")
    obj.ConfigurationName = "test"
    obj.IamRoleArn = "arn:aws:iam::123456789012:role/test"
    obj.SlackChannelId = "C1234567890"
    obj.SlackWorkspaceId = "T1234567890"
    
    # Valid list values should work
    obj.GuardrailPolicies = policies
    obj.SnsTopicArns = sns_arns
    assert obj.properties.get("GuardrailPolicies") == policies
    assert obj.properties.get("SnsTopicArns") == sns_arns
    
    # Non-list values should raise TypeError
    with pytest.raises(TypeError):
        obj.GuardrailPolicies = invalid_value