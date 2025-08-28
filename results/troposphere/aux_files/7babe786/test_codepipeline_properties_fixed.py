"""Property-based tests for troposphere.codepipeline module (fixed)"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, settings, assume
import troposphere.codepipeline as cp
import json
import string


# Strategy for generating valid ASCII alphanumeric titles (to match library's expectation)
ascii_title_strategy = st.text(alphabet=string.ascii_letters + string.digits, min_size=1, max_size=50)

# Strategy for integers
positive_int_strategy = st.integers(min_value=0, max_value=1000)

# Strategy for simple string values
string_strategy = st.text(min_size=1, max_size=100)


@given(
    title=ascii_title_strategy,
    max_count=positive_int_strategy,
    min_count=positive_int_strategy
)
def test_artifact_details_round_trip(title, max_count, min_count):
    """Test that ArtifactDetails can be converted to dict and back"""
    # Create object
    artifact = cp.ArtifactDetails(
        title=title,
        MaximumCount=max_count,
        MinimumCount=min_count
    )
    
    # Convert to dict
    dict_repr = artifact.to_dict()
    
    # Create new object from dict
    reconstructed = cp.ArtifactDetails.from_dict(title, dict_repr)
    
    # They should be equal
    assert artifact == reconstructed
    assert artifact.to_dict() == reconstructed.to_dict()


@given(
    title=ascii_title_strategy,
    id_str=string_strategy,
    type_str=string_strategy
)
def test_encryption_key_round_trip(title, id_str, type_str):
    """Test that EncryptionKey can be converted to dict and back"""
    # Create object
    key = cp.EncryptionKey(
        title=title,
        Id=id_str,
        Type=type_str
    )
    
    # Convert to dict
    dict_repr = key.to_dict()
    
    # Create new object from dict
    reconstructed = cp.EncryptionKey.from_dict(title, dict_repr)
    
    # They should be equal
    assert key == reconstructed
    assert key.to_dict() == reconstructed.to_dict()


@given(
    title=ascii_title_strategy,
    category=st.sampled_from(['Source', 'Build', 'Deploy', 'Test', 'Invoke', 'Approval']),
    owner=st.sampled_from(['AWS', 'ThirdParty', 'Custom']),
    provider=string_strategy,
    version=st.from_regex(r'[1-9][0-9]{0,2}', fullmatch=True)
)
def test_action_type_id_round_trip(title, category, owner, provider, version):
    """Test that ActionTypeId can be converted to dict and back"""
    # Create object
    action_type = cp.ActionTypeId(
        title=title,
        Category=category,
        Owner=owner,
        Provider=provider,
        Version=version
    )
    
    # Convert to dict
    dict_repr = action_type.to_dict()
    
    # Create new object from dict
    reconstructed = cp.ActionTypeId.from_dict(title, dict_repr)
    
    # They should be equal
    assert action_type == reconstructed
    assert action_type.to_dict() == reconstructed.to_dict()


@given(
    title=ascii_title_strategy,
    json_path=string_strategy,
    match_equals=st.one_of(st.none(), string_strategy)
)
def test_webhook_filter_rule_round_trip(title, json_path, match_equals):
    """Test that WebhookFilterRule can be converted to dict and back"""
    # JsonPath is required, MatchEquals is optional
    kwargs = {'JsonPath': json_path}
    if match_equals is not None:
        kwargs['MatchEquals'] = match_equals
    
    rule = cp.WebhookFilterRule(title=title, **kwargs)
    
    # Convert to dict
    dict_repr = rule.to_dict()
    
    # Create new object from dict
    reconstructed = cp.WebhookFilterRule.from_dict(title, dict_repr)
    
    # They should be equal
    assert rule == reconstructed
    assert rule.to_dict() == reconstructed.to_dict()


# Test for special characters in property values (not titles)
@given(
    name=st.text(min_size=1, max_size=100),  # Allow any Unicode in names
    value=st.text(min_size=1, max_size=100),  # Allow any Unicode in values
    type_str=st.sampled_from(['PLAINTEXT', 'PARAMETER_STORE', 'SECRETS_MANAGER'])
)
def test_environment_variable_unicode_values(name, value, type_str):
    """Test that EnvironmentVariable handles Unicode in property values"""
    # Create object (Name and Value are required, Type is optional)
    env_var = cp.EnvironmentVariable(
        Name=name,
        Value=value,
        Type=type_str
    )
    
    # Convert to dict
    dict_repr = env_var.to_dict()
    
    # Create new object from dict
    reconstructed = cp.EnvironmentVariable.from_dict(None, dict_repr)
    
    # They should be equal
    assert env_var == reconstructed
    assert env_var.to_dict() == reconstructed.to_dict()


# Test edge cases for integer values
@given(
    title=ascii_title_strategy,
    max_count=st.integers(),  # Allow any integer, including negative
    min_count=st.integers()
)
def test_artifact_details_integer_edge_cases(title, max_count, min_count):
    """Test that ArtifactDetails handles integer edge cases"""
    # Create object
    artifact = cp.ArtifactDetails(
        title=title,
        MaximumCount=max_count,
        MinimumCount=min_count
    )
    
    # Convert to dict
    dict_repr = artifact.to_dict()
    
    # The values should be preserved
    assert dict_repr['MaximumCount'] == max_count
    assert dict_repr['MinimumCount'] == min_count
    
    # And round-trip should work
    reconstructed = cp.ArtifactDetails.from_dict(title, dict_repr)
    assert artifact == reconstructed


# Test empty strings where allowed
@given(
    title=ascii_title_strategy,
    description=st.text(min_size=0, max_size=100),  # Allow empty string
    key=st.booleans(),
    name=st.text(min_size=1, max_size=100),  # Name is required, can't be empty
    queryable=st.booleans(),
    required=st.booleans(),
    secret=st.booleans(),
    type_str=st.one_of(st.just(''), st.sampled_from(['String', 'StringList', 'Number', 'Boolean']))
)
def test_configuration_properties_empty_strings(title, description, key, name, queryable, required, secret, type_str):
    """Test that ConfigurationProperties handles empty strings appropriately"""
    # Create object
    kwargs = {
        'Key': key,
        'Name': name,
        'Queryable': queryable,
        'Required': required,
        'Secret': secret
    }
    if description:  # Only add if non-empty
        kwargs['Description'] = description
    if type_str:  # Only add if non-empty
        kwargs['Type'] = type_str
        
    config = cp.ConfigurationProperties(title=title, **kwargs)
    
    # Convert to dict
    dict_repr = config.to_dict()
    
    # Create new object from dict  
    reconstructed = cp.ConfigurationProperties.from_dict(title, dict_repr)
    
    # They should be equal
    assert config == reconstructed
    assert config.to_dict() == reconstructed.to_dict()