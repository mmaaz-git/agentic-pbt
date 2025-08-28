#!/usr/bin/env /root/hypothesis-llm/envs/troposphere_env/bin/python

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import pytest
from troposphere import apigatewayv2
from troposphere.validators.apigatewayv2 import (
    validate_timeout_in_millis,
    validate_authorizer_ttl,
    validate_integration_type,
    validate_authorizer_type,
    validate_logging_level,
    validate_passthrough_behavior,
    validate_content_handling_strategy,
    dict_or_string,
)
from troposphere import BaseAWSObject, AWSProperty


# Property 1: timeout_in_millis must be >= 50
@given(st.integers())
def test_timeout_validation_boundary(timeout):
    """Test that validate_timeout_in_millis correctly enforces the >= 50 constraint"""
    if timeout < 50:
        with pytest.raises(ValueError, match="must be greater than 50"):
            validate_timeout_in_millis(timeout)
    else:
        # Should not raise for valid values
        result = validate_timeout_in_millis(timeout)
        assert result == timeout


# Property 2: authorizer_ttl must be positive and <= 3600
@given(st.integers())
def test_authorizer_ttl_boundary(ttl):
    """Test that validate_authorizer_ttl correctly enforces 0 < ttl <= 3600"""
    try:
        result = validate_authorizer_ttl(ttl)
        # If it succeeds, verify the constraints are met
        assert 0 < result <= 3600
        assert result == ttl
    except (ValueError, TypeError):
        # Should fail for negative, zero, or > 3600
        assert ttl <= 0 or ttl > 3600


# Property 3: Integration type enum validation
@given(st.text())
def test_integration_type_enum(integration_type):
    """Test that only valid integration types are accepted"""
    valid_types = ["AWS", "AWS_PROXY", "HTTP", "HTTP_PROXY", "MOCK"]
    if integration_type in valid_types:
        result = validate_integration_type(integration_type)
        assert result == integration_type
    else:
        with pytest.raises(ValueError, match="is not a valid IntegrationType"):
            validate_integration_type(integration_type)


# Property 4: Authorizer type enum validation
@given(st.text())
def test_authorizer_type_enum(auth_type):
    """Test that only valid authorizer types are accepted"""
    valid_types = ["REQUEST", "JWT"]
    if auth_type in valid_types:
        result = validate_authorizer_type(auth_type)
        assert result == auth_type
    else:
        with pytest.raises(ValueError, match="is not a valid AuthorizerType"):
            validate_authorizer_type(auth_type)


# Property 5: dict_or_string type validation
@given(st.one_of(st.dictionaries(st.text(), st.text()), st.text(), st.integers(), st.lists(st.text())))
def test_dict_or_string_validation(value):
    """Test that dict_or_string only accepts dict or str types"""
    if isinstance(value, (dict, str)):
        result = dict_or_string(value)
        assert result == value
    else:
        with pytest.raises(TypeError, match="must be either dict or str"):
            dict_or_string(value)


# Property 6: Title validation - must be alphanumeric
@given(st.text())
def test_title_validation(title):
    """Test that resource titles must be alphanumeric"""
    import re
    valid_names = re.compile(r"^[a-zA-Z0-9]+$")
    
    # Create a mock object to test title validation
    class TestResource(BaseAWSObject):
        resource_type = "Test::Resource"
        props = {}
    
    if title and valid_names.match(title):
        # Should succeed for valid alphanumeric titles
        obj = TestResource(title=title, validation=True)
        assert obj.title == title
    else:
        # Should fail for non-alphanumeric or empty titles
        with pytest.raises(ValueError, match='Name .* not alphanumeric'):
            TestResource(title=title, validation=True)


# Property 7: Round-trip property for AWS objects
@given(
    st.text(min_size=1).filter(lambda x: x.isalnum()),  # Valid title
    st.text(),  # Description
    st.text(),  # Stage name
)
def test_deployment_round_trip(title, description, stage_name):
    """Test that Deployment objects can round-trip through to_dict/from_dict"""
    # Create a Deployment object
    deployment = apigatewayv2.Deployment(
        title=title,
        ApiId="test-api-id",
        Description=description,
        StageName=stage_name
    )
    
    # Convert to dict
    deployment_dict = deployment.to_dict()
    
    # The dict should contain the properties we set
    assert deployment_dict["Type"] == "AWS::ApiGatewayV2::Deployment"
    assert deployment_dict["Properties"]["ApiId"] == "test-api-id"
    
    if description:
        assert deployment_dict["Properties"]["Description"] == description
    if stage_name:
        assert deployment_dict["Properties"]["StageName"] == stage_name
    
    # Try to recreate from dict (via _from_dict)
    new_deployment = apigatewayv2.Deployment._from_dict(
        title=title,
        **deployment_dict["Properties"]
    )
    
    # The new object should have the same properties
    assert new_deployment.to_dict() == deployment_dict


# Property 8: Content handling strategy enum
@given(st.text())
def test_content_handling_strategy_enum(strategy):
    """Test that only valid content handling strategies are accepted"""
    valid_strategies = ["CONVERT_TO_TEXT", "CONVERT_TO_BINARY"]
    if strategy in valid_strategies:
        result = validate_content_handling_strategy(strategy)
        assert result == strategy
    else:
        with pytest.raises(ValueError, match="is not a valid ContentHandlingStrategy"):
            validate_content_handling_strategy(strategy)


# Property 9: Properties marked as required must be present
@given(
    st.text(min_size=1).filter(lambda x: x.isalnum()),  # Valid title
    st.booleans(),  # Include ApiId?
    st.booleans(),  # Include DomainName?
    st.booleans(),  # Include Stage?
)
def test_required_properties(title, include_api_id, include_domain, include_stage):
    """Test that required properties are enforced in ApiMapping"""
    kwargs = {}
    if include_api_id:
        kwargs["ApiId"] = "test-api"
    if include_domain:
        kwargs["DomainName"] = "test.example.com"
    if include_stage:
        kwargs["Stage"] = "prod"
    
    # ApiMapping requires ApiId, DomainName, and Stage
    mapping = apigatewayv2.ApiMapping(title=title, validation=False, **kwargs)
    
    # When validating, it should check for required properties
    if include_api_id and include_domain and include_stage:
        # All required properties present, should validate successfully
        mapping.to_dict(validation=True)
    else:
        # Missing required properties, should fail validation
        with pytest.raises(ValueError):
            mapping.to_dict(validation=True)


if __name__ == "__main__":
    # Run with pytest for better output
    pytest.main([__file__, "-v", "--tb=short"])