"""Advanced property-based tests for troposphere.appsync module - hunting for edge cases"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings, example
import pytest
from troposphere import appsync, validators
from troposphere.validators.appsync import resolver_kind_validator
import json


# Test 1: Edge cases in resolver_kind_validator with special strings
@given(st.one_of(
    st.text(),  # General text
    st.just("unit"),  # Lowercase version
    st.just("UNIT "),  # With whitespace
    st.just(" UNIT"),  # Leading whitespace
    st.just("pipeline"),  # Lowercase
    st.just("PIPELINE\n"),  # With newline
    st.just(""),  # Empty string
    st.just(None),  # None value
))
def test_resolver_kind_validator_edge_cases(value):
    """Test resolver_kind_validator with edge cases and special strings"""
    valid_values = ["UNIT", "PIPELINE"]
    
    try:
        if value in valid_values:
            result = resolver_kind_validator(value)
            assert result == value
        else:
            # Should raise for anything not exactly matching valid values
            with pytest.raises((ValueError, TypeError, AttributeError)):
                resolver_kind_validator(value)
    except (TypeError, AttributeError):
        # None or non-string values might cause these
        pass


# Test 2: Test title validation for AWS objects
@given(st.one_of(
    st.text(),
    st.text(alphabet="!@#$%^&*()[]{}|\\/<>?,.~`", min_size=1),  # Special chars
    st.text(min_size=256),  # Very long names
    st.just(""),  # Empty
    st.just("123abc"),  # Starting with numbers
    st.just("abc-123"),  # With hyphens
    st.just("abc_123"),  # With underscores
    st.just("ABC123"),  # Valid alphanumeric
))
def test_aws_object_title_validation(title):
    """Test that AWS object title validation works correctly"""
    try:
        obj = appsync.Api(
            title,
            Name="TestApi"
        )
        # If it didn't raise, the title should be alphanumeric only
        assert title.isalnum() or title is None
    except ValueError as e:
        # Should only raise ValueError for invalid names
        assert "not alphanumeric" in str(e)
        # Invalid names should not be alphanumeric
        if title:
            assert not title.isalnum()


# Test 3: Test property type validation with wrong types
@given(
    ttl_value=st.one_of(
        st.floats(allow_nan=True, allow_infinity=True),
        st.text(),
        st.integers(),
        st.booleans(),
        st.none(),
        st.lists(st.integers()),
    )
)
def test_api_cache_ttl_type_validation(ttl_value):
    """Test that ApiCache TTL property validates type correctly"""
    try:
        cache = appsync.ApiCache(
            "TestCache",
            ApiCachingBehavior="FULL_REQUEST_CACHING",
            ApiId="test-api",
            Ttl=ttl_value,  # Should be a double/float
            Type="SMALL"
        )
        
        # If it succeeded, check the value was acceptable
        result = cache.to_dict()
        
        # The value should have been converted or accepted
        if isinstance(ttl_value, (int, float)) and not (ttl_value != ttl_value):  # not NaN
            assert "Ttl" in result["Properties"]
    except (TypeError, ValueError) as e:
        # Invalid types should raise errors
        pass


# Test 4: Test lists with invalid element types
@given(
    auth_providers=st.lists(
        st.one_of(
            st.builds(appsync.AuthProvider, AuthType=st.text(min_size=1)),
            st.text(),  # Wrong type
            st.integers(),  # Wrong type
            st.none(),  # None
        ),
        min_size=1,
        max_size=3
    )
)
def test_event_config_invalid_list_elements(auth_providers):
    """Test EventConfig with potentially invalid list elements"""
    try:
        # Filter to only valid AuthProvider objects
        valid_providers = [p for p in auth_providers if isinstance(p, appsync.AuthProvider)]
        invalid_providers = [p for p in auth_providers if not isinstance(p, appsync.AuthProvider)]
        
        if invalid_providers:
            # Should fail with invalid providers
            with pytest.raises((TypeError, AttributeError)):
                event_config = appsync.EventConfig(
                    AuthProviders=auth_providers,
                    ConnectionAuthModes=[appsync.AuthMode(AuthType="TEST")],
                    DefaultPublishAuthModes=[appsync.AuthMode(AuthType="TEST")],
                    DefaultSubscribeAuthModes=[appsync.AuthMode(AuthType="TEST")]
                )
        else:
            # Should succeed with only valid providers
            event_config = appsync.EventConfig(
                AuthProviders=auth_providers,
                ConnectionAuthModes=[appsync.AuthMode(AuthType="TEST")],
                DefaultPublishAuthModes=[appsync.AuthMode(AuthType="TEST")],
                DefaultSubscribeAuthModes=[appsync.AuthMode(AuthType="TEST")]
            )
            assert len(event_config.AuthProviders) == len(valid_providers)
    except (TypeError, AttributeError):
        # Expected for invalid inputs
        pass


# Test 5: Test missing required properties
@given(
    include_region=st.booleans(),
    include_user_pool=st.booleans(),
    include_regex=st.booleans()
)
def test_cognito_config_missing_required(include_region, include_user_pool, include_regex):
    """Test CognitoConfig behavior when required properties are missing"""
    kwargs = {}
    
    if include_region:
        kwargs["AwsRegion"] = "us-east-1"
    if include_user_pool:
        kwargs["UserPoolId"] = "test-pool"
    if include_regex:
        kwargs["AppIdClientRegex"] = ".*"
    
    if include_region and include_user_pool:
        # Should succeed with both required fields
        config = appsync.CognitoConfig(**kwargs)
        assert config.AwsRegion == "us-east-1"
        assert config.UserPoolId == "test-pool"
    else:
        # Missing required fields - to_dict validation should catch this
        config = appsync.CognitoConfig(**kwargs)
        # Validation happens in to_dict()
        try:
            result = config.to_dict()
            # If it succeeded, check what we got
            if "AwsRegion" not in result and "UserPoolId" not in result:
                # Both missing - might be allowed due to no validation
                pass
        except (KeyError, AttributeError):
            # Expected when required fields are missing
            pass


# Test 6: Test deeply nested structures
@given(
    table_name=st.text(min_size=1),
    use_caller_creds=st.booleans(),
    versioned=st.booleans(),
    include_delta_sync=st.booleans()
)
def test_dynamodb_config_nested_properties(table_name, use_caller_creds, versioned, include_delta_sync):
    """Test DynamoDBConfig with nested DeltaSyncConfig"""
    config_dict = {
        "AwsRegion": "us-east-1",
        "TableName": table_name,
        "UseCallerCredentials": use_caller_creds,
        "Versioned": versioned
    }
    
    if include_delta_sync:
        delta_config = appsync.DeltaSyncConfig(
            BaseTableTTL="86400",
            DeltaSyncTableName=f"delta_{table_name}",
            DeltaSyncTableTTL="3600"
        )
        config_dict["DeltaSyncConfig"] = delta_config
    
    dynamo_config = appsync.DynamoDBConfig(**config_dict)
    
    assert dynamo_config.TableName == table_name
    assert dynamo_config.UseCallerCredentials == use_caller_creds
    assert dynamo_config.Versioned == versioned
    
    result = dynamo_config.to_dict()
    assert result["TableName"] == table_name
    
    if include_delta_sync:
        assert "DeltaSyncConfig" in result
        assert result["DeltaSyncConfig"]["DeltaSyncTableName"] == f"delta_{table_name}"


# Test 7: Test integer limit properties with boundary values
@given(
    query_limit=st.one_of(
        st.just(0),  # Below minimum
        st.just(-1),  # Negative
        st.just(76),  # Above typical max
        st.just(2**31),  # Very large
        st.floats(),  # Wrong type
    )
)
def test_graphql_api_query_depth_limit_boundaries(query_limit):
    """Test GraphQLApi QueryDepthLimit with boundary values"""
    try:
        api = appsync.GraphQLApi(
            "TestAPI",
            Name="TestAPI",
            AuthenticationType="API_KEY",
            QueryDepthLimit=query_limit
        )
        
        # If it succeeded, the value was accepted
        result = api.to_dict()
        
        # Check if the value is in the result
        if "QueryDepthLimit" in result.get("Properties", {}):
            stored_value = result["Properties"]["QueryDepthLimit"]
            # Integer limits should be preserved
            if isinstance(query_limit, int):
                assert stored_value == query_limit
    except (TypeError, ValueError):
        # Invalid types or values might raise
        pass


# Test 8: Test S3 location alternatives
@given(
    use_code=st.booleans(),
    use_s3=st.booleans(),
    code_value=st.text(min_size=1),
    s3_value=st.text(min_size=1)
)
def test_function_config_code_alternatives(use_code, use_s3, code_value, s3_value):
    """Test FunctionConfiguration with Code vs CodeS3Location"""
    kwargs = {
        "ApiId": "test-api",
        "DataSourceName": "test-source",
        "Name": "TestFunction"
    }
    
    if use_code:
        kwargs["Code"] = code_value
    if use_s3:
        kwargs["CodeS3Location"] = s3_value
    
    # Both or neither should work
    func = appsync.FunctionConfiguration("TestFunc", **kwargs)
    
    if use_code:
        assert func.Code == code_value
    if use_s3:
        assert func.CodeS3Location == s3_value
    
    result = func.to_dict()
    assert result["Type"] == "AWS::AppSync::FunctionConfiguration"


# Test 9: Test property name case sensitivity
@given(st.data())
def test_property_case_sensitivity(data):
    """Test if property names are case sensitive"""
    auth_type = data.draw(st.text(min_size=1))
    
    # Try with correct case
    auth1 = appsync.AuthMode(AuthType=auth_type)
    assert auth1.AuthType == auth_type
    
    # Try with wrong case - should fail
    try:
        auth2 = appsync.AuthMode(authtype=auth_type)  # lowercase
        # If it succeeded, it shouldn't have the property
        with pytest.raises(AttributeError):
            _ = auth2.AuthType
    except (AttributeError, TypeError):
        # Expected - property names should be case sensitive
        pass


# Test 10: Test with Unicode and special characters in string properties
@given(
    name=st.one_of(
        st.just(""),  # Empty
        st.just("テスト"),  # Japanese
        st.just("🚀🌟"),  # Emojis  
        st.just("test\x00name"),  # Null byte
        st.just("test\nname"),  # Newline
        st.just("test\tname"),  # Tab
        st.text(alphabet="你好世界"),  # Chinese
        st.text(min_size=1000),  # Very long
    )
)
def test_api_name_unicode_characters(name):
    """Test Api with various Unicode and special characters in Name"""
    try:
        api = appsync.Api(
            "TestApi",  # Valid title
            Name=name  # Potentially problematic name
        )
        
        # If it succeeded, check the name is preserved
        assert api.Name == name
        
        result = api.to_dict()
        assert result["Properties"]["Name"] == name
    except (ValueError, UnicodeError):
        # Some characters might not be allowed
        pass