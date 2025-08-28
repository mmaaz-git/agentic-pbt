"""Property-based tests for troposphere.codepipeline module"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, settings, assume
import troposphere.codepipeline as cp
import json


# Strategy for generating valid alphanumeric titles  
title_strategy = st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')), min_size=1, max_size=50)

# Strategy for integers
positive_int_strategy = st.integers(min_value=0, max_value=1000)

# Strategy for simple string values
string_strategy = st.text(min_size=1, max_size=100)


@given(
    title=title_strategy,
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
    title=title_strategy,
    description=string_strategy,
    key=st.booleans(),
    name=string_strategy,
    queryable=st.booleans(),
    required=st.booleans(),
    secret=st.booleans(),
    type_str=st.sampled_from(['String', 'StringList', 'Number', 'Boolean'])
)
def test_configuration_properties_round_trip(title, description, key, name, queryable, required, secret, type_str):
    """Test that ConfigurationProperties can be converted to dict and back"""
    # Create object
    config = cp.ConfigurationProperties(
        title=title,
        Description=description,
        Key=key,
        Name=name,
        Queryable=queryable,
        Required=required,
        Secret=secret,
        Type=type_str
    )
    
    # Convert to dict
    dict_repr = config.to_dict()
    
    # Create new object from dict  
    reconstructed = cp.ConfigurationProperties.from_dict(title, dict_repr)
    
    # They should be equal
    assert config == reconstructed
    assert config.to_dict() == reconstructed.to_dict()


@given(title=st.text(min_size=1))
def test_title_validation(title):
    """Test that title validation works as expected"""
    # Title must be alphanumeric only according to the code
    # Let's test that non-alphanumeric titles raise ValueError
    
    try:
        artifact = cp.ArtifactDetails(
            title=title,
            MaximumCount=1,
            MinimumCount=0
        )
        # If it succeeded, title should be alphanumeric
        assert title.replace('_', '').isalnum() or all(c.isalnum() for c in title)
    except ValueError as e:
        # Should fail if title is not alphanumeric
        assert "not alphanumeric" in str(e)
        assert not all(c.isalnum() for c in title)


@given(
    max_count=positive_int_strategy,
    min_count=positive_int_strategy
)  
def test_artifact_details_required_fields(max_count, min_count):
    """Test that ArtifactDetails validates required fields"""
    # Both MaximumCount and MinimumCount are required
    
    # Should work with both fields
    artifact = cp.ArtifactDetails(
        MaximumCount=max_count,
        MinimumCount=min_count
    )
    dict_repr = artifact.to_dict()
    assert 'MaximumCount' in dict_repr
    assert 'MinimumCount' in dict_repr
    
    # Test missing MaximumCount
    try:
        artifact_missing_max = cp.ArtifactDetails(
            MinimumCount=min_count
        )
        # This should fail when calling to_dict with validation
        artifact_missing_max.to_dict()
        assert False, "Should have raised ValueError for missing MaximumCount"
    except ValueError as e:
        assert "MaximumCount" in str(e) and "required" in str(e)
    
    # Test missing MinimumCount
    try:
        artifact_missing_min = cp.ArtifactDetails(
            MaximumCount=max_count
        )
        # This should fail when calling to_dict with validation
        artifact_missing_min.to_dict()
        assert False, "Should have raised ValueError for missing MinimumCount"
    except ValueError as e:
        assert "MinimumCount" in str(e) and "required" in str(e)


@given(
    title=title_strategy,
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
    title=title_strategy,
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
    title=title_strategy,
    excludes=st.lists(string_strategy, min_size=0, max_size=5),
    includes=st.lists(string_strategy, min_size=0, max_size=5)
)
def test_git_branch_filter_criteria_round_trip(title, excludes, includes):
    """Test that GitBranchFilterCriteria can be converted to dict and back"""
    # Create object with optional fields
    kwargs = {}
    if excludes:
        kwargs['Excludes'] = excludes
    if includes:
        kwargs['Includes'] = includes
    
    if not kwargs:
        # Must have at least one field
        kwargs['Includes'] = ['main']
    
    criteria = cp.GitBranchFilterCriteria(title=title, **kwargs)
    
    # Convert to dict
    dict_repr = criteria.to_dict()
    
    # Create new object from dict
    reconstructed = cp.GitBranchFilterCriteria.from_dict(title, dict_repr)
    
    # They should be equal
    assert criteria == reconstructed
    assert criteria.to_dict() == reconstructed.to_dict()


@given(
    name=string_strategy,
    value=string_strategy,
    type_str=st.sampled_from(['PLAINTEXT', 'PARAMETER_STORE', 'SECRETS_MANAGER'])
)
def test_environment_variable_round_trip(name, value, type_str):
    """Test that EnvironmentVariable can be converted to dict and back"""
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


@given(
    location=string_strategy,
    type_str=st.just('S3')  # Only S3 is supported currently
)
def test_artifact_store_required_fields(location, type_str):
    """Test that ArtifactStore validates required fields"""
    # Location and Type are required
    
    # Should work with required fields
    store = cp.ArtifactStore(
        Location=location,
        Type=type_str
    )
    dict_repr = store.to_dict()
    assert 'Location' in dict_repr
    assert 'Type' in dict_repr
    
    # Test missing Location
    try:
        store_missing_location = cp.ArtifactStore(
            Type=type_str
        )
        store_missing_location.to_dict()
        assert False, "Should have raised ValueError for missing Location"
    except ValueError as e:
        assert "Location" in str(e) and "required" in str(e)
    
    # Test missing Type
    try:
        store_missing_type = cp.ArtifactStore(
            Location=location
        )
        store_missing_type.to_dict()
        assert False, "Should have raised ValueError for missing Type"
    except ValueError as e:
        assert "Type" in str(e) and "required" in str(e)


@given(
    title=title_strategy,
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