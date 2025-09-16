"""Property-based tests for troposphere.appsync module"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import pytest
from troposphere import appsync
from troposphere.validators.appsync import resolver_kind_validator


# Test 1: resolver_kind_validator should only accept "UNIT" or "PIPELINE"
@given(st.text())
def test_resolver_kind_validator_property(value):
    """Test that resolver_kind_validator accepts only valid values as documented"""
    valid_values = ["UNIT", "PIPELINE"]
    
    if value in valid_values:
        # Should not raise exception for valid values
        result = resolver_kind_validator(value)
        assert result == value
    else:
        # Should raise ValueError for invalid values
        with pytest.raises(ValueError) as exc_info:
            resolver_kind_validator(value)
        assert "Kind must be one of:" in str(exc_info.value)


# Test 2: Required vs optional properties for AWS objects
@given(
    api_id=st.text(min_size=1),
    field_name=st.text(min_size=1),
    type_name=st.text(min_size=1),
    optional_kind=st.one_of(st.none(), st.sampled_from(["UNIT", "PIPELINE"])),
    optional_code=st.one_of(st.none(), st.text())
)
def test_resolver_required_optional_properties(api_id, field_name, type_name, optional_kind, optional_code):
    """Test that Resolver correctly handles required and optional properties"""
    # According to the code, ApiId, FieldName, and TypeName are required (marked True)
    # Kind, Code, etc. are optional (marked False)
    
    # Should work with required fields
    resolver = appsync.Resolver(
        "TestResolver",
        ApiId=api_id,
        FieldName=field_name,
        TypeName=type_name
    )
    
    # Check required fields are set
    assert resolver.ApiId == api_id
    assert resolver.FieldName == field_name
    assert resolver.TypeName == type_name
    
    # Test optional fields
    if optional_kind:
        resolver.Kind = optional_kind
        assert resolver.Kind == optional_kind
    
    if optional_code:
        resolver.Code = optional_code
        assert resolver.Code == optional_code
    
    # to_dict should include all set properties
    result_dict = resolver.to_dict()
    assert result_dict["Type"] == "AWS::AppSync::Resolver"
    assert result_dict["Properties"]["ApiId"] == api_id
    assert result_dict["Properties"]["FieldName"] == field_name
    assert result_dict["Properties"]["TypeName"] == type_name


# Test 3: Round-trip property for AWSProperty classes
@given(
    auth_type=st.text(min_size=1)
)
def test_auth_mode_round_trip(auth_type):
    """Test that AuthMode preserves data through creation and to_dict"""
    auth_mode = appsync.AuthMode(AuthType=auth_type)
    
    # Property should be accessible
    assert auth_mode.AuthType == auth_type
    
    # to_dict should preserve the property
    dict_repr = auth_mode.to_dict()
    assert dict_repr["AuthType"] == auth_type


# Test 4: CognitoConfig required vs optional properties
@given(
    aws_region=st.text(min_size=1),
    user_pool_id=st.text(min_size=1),
    optional_regex=st.one_of(st.none(), st.text())
)
def test_cognito_config_properties(aws_region, user_pool_id, optional_regex):
    """Test CognitoConfig handles required AwsRegion and UserPoolId correctly"""
    # According to props, AwsRegion and UserPoolId are required (True)
    # AppIdClientRegex is optional (False)
    
    if optional_regex:
        config = appsync.CognitoConfig(
            AwsRegion=aws_region,
            UserPoolId=user_pool_id,
            AppIdClientRegex=optional_regex
        )
        assert config.AppIdClientRegex == optional_regex
    else:
        config = appsync.CognitoConfig(
            AwsRegion=aws_region,
            UserPoolId=user_pool_id
        )
    
    assert config.AwsRegion == aws_region
    assert config.UserPoolId == user_pool_id
    
    dict_repr = config.to_dict()
    assert dict_repr["AwsRegion"] == aws_region
    assert dict_repr["UserPoolId"] == user_pool_id


# Test 5: ApiCache numeric properties
@given(
    api_caching_behavior=st.text(min_size=1),
    api_id=st.text(min_size=1),
    ttl=st.floats(min_value=0, max_value=3600, allow_nan=False, allow_infinity=False),
    cache_type=st.text(min_size=1),
    at_rest_encryption=st.one_of(st.none(), st.booleans())
)
def test_api_cache_numeric_properties(api_caching_behavior, api_id, ttl, cache_type, at_rest_encryption):
    """Test ApiCache handles numeric TTL and boolean properties correctly"""
    kwargs = {
        "ApiCachingBehavior": api_caching_behavior,
        "ApiId": api_id,
        "Ttl": ttl,  # This is a double according to props
        "Type": cache_type
    }
    
    if at_rest_encryption is not None:
        kwargs["AtRestEncryptionEnabled"] = at_rest_encryption
    
    cache = appsync.ApiCache("TestCache", **kwargs)
    
    assert cache.ApiCachingBehavior == api_caching_behavior
    assert cache.ApiId == api_id
    assert cache.Ttl == ttl
    assert cache.Type == cache_type
    
    if at_rest_encryption is not None:
        assert cache.AtRestEncryptionEnabled == at_rest_encryption


# Test 6: Lists of complex types
@given(
    auth_providers_count=st.integers(min_value=0, max_value=5)
)
def test_event_config_list_properties(auth_providers_count):
    """Test that EventConfig correctly handles lists of AuthProvider objects"""
    auth_providers = []
    for i in range(auth_providers_count):
        provider = appsync.AuthProvider(
            AuthType=f"Type{i}"
        )
        auth_providers.append(provider)
    
    connection_auth_modes = [
        appsync.AuthMode(AuthType="ConnectionAuth")
    ]
    
    default_publish_modes = [
        appsync.AuthMode(AuthType="PublishAuth")
    ]
    
    default_subscribe_modes = [
        appsync.AuthMode(AuthType="SubscribeAuth")
    ]
    
    event_config = appsync.EventConfig(
        AuthProviders=auth_providers,
        ConnectionAuthModes=connection_auth_modes,
        DefaultPublishAuthModes=default_publish_modes,
        DefaultSubscribeAuthModes=default_subscribe_modes
    )
    
    # Verify lists are preserved
    assert len(event_config.AuthProviders) == auth_providers_count
    assert len(event_config.ConnectionAuthModes) == 1
    assert len(event_config.DefaultPublishAuthModes) == 1
    assert len(event_config.DefaultSubscribeAuthModes) == 1
    
    # Test to_dict preserves structure
    dict_repr = event_config.to_dict()
    assert len(dict_repr["AuthProviders"]) == auth_providers_count


# Test 7: DeltaSyncConfig string properties
@given(
    base_ttl=st.text(min_size=1),
    table_name=st.text(min_size=1),
    delta_ttl=st.text(min_size=1)
)
def test_delta_sync_config_all_required(base_ttl, table_name, delta_ttl):
    """Test that DeltaSyncConfig requires all three properties"""
    # All three properties are marked as required (True)
    config = appsync.DeltaSyncConfig(
        BaseTableTTL=base_ttl,
        DeltaSyncTableName=table_name,
        DeltaSyncTableTTL=delta_ttl
    )
    
    assert config.BaseTableTTL == base_ttl
    assert config.DeltaSyncTableName == table_name
    assert config.DeltaSyncTableTTL == delta_ttl
    
    dict_repr = config.to_dict()
    assert dict_repr["BaseTableTTL"] == base_ttl
    assert dict_repr["DeltaSyncTableName"] == table_name
    assert dict_repr["DeltaSyncTableTTL"] == delta_ttl


# Test 8: GraphQLApi with integer limits
@given(
    name=st.text(min_size=1),
    auth_type=st.text(min_size=1),
    query_depth_limit=st.one_of(st.none(), st.integers(min_value=1, max_value=75)),
    resolver_count_limit=st.one_of(st.none(), st.integers(min_value=1, max_value=10000))
)
def test_graphql_api_integer_properties(name, auth_type, query_depth_limit, resolver_count_limit):
    """Test GraphQLApi handles integer limit properties correctly"""
    kwargs = {
        "Name": name,
        "AuthenticationType": auth_type
    }
    
    if query_depth_limit is not None:
        kwargs["QueryDepthLimit"] = query_depth_limit
    
    if resolver_count_limit is not None:
        kwargs["ResolverCountLimit"] = resolver_count_limit
    
    api = appsync.GraphQLApi("TestAPI", **kwargs)
    
    assert api.Name == name
    assert api.AuthenticationType == auth_type
    
    if query_depth_limit is not None:
        assert api.QueryDepthLimit == query_depth_limit
    
    if resolver_count_limit is not None:
        assert api.ResolverCountLimit == resolver_count_limit
    
    dict_repr = api.to_dict()
    assert dict_repr["Type"] == "AWS::AppSync::GraphQLApi"
    assert dict_repr["Properties"]["Name"] == name