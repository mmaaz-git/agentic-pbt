import json
import re
from hypothesis import given, strategies as st, assume, settings
import troposphere.codestarconnections as csc
from troposphere import Tags


# Strategy for valid alphanumeric titles
valid_title_strategy = st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')), min_size=1, max_size=100)

# Strategy for provider types
provider_type_strategy = st.sampled_from(["Bitbucket", "GitHub", "GitHubEnterpriseServer"])

# Strategy for invalid provider types 
invalid_provider_type_strategy = st.text(min_size=1).filter(lambda x: x not in ["Bitbucket", "GitHub", "GitHubEnterpriseServer"])

# Strategy for ARN-like strings
arn_strategy = st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')), min_size=1, max_size=100).map(lambda x: f"arn:aws:codestar-connections:us-east-1:123456789012:{x}")

# Strategy for simple strings
simple_string_strategy = st.text(min_size=1, max_size=100)


@given(title=valid_title_strategy, 
       connection_name=simple_string_strategy,
       provider_type=provider_type_strategy)
def test_connection_roundtrip_to_dict_from_dict(title, connection_name, provider_type):
    """Test that Connection objects survive dict conversion roundtrip"""
    # Create connection
    conn1 = csc.Connection(
        title=title,
        ConnectionName=connection_name,
        ProviderType=provider_type
    )
    
    # Convert to dict and back
    conn_dict = conn1.to_dict()
    
    # Extract properties from dict
    props = conn_dict.get("Properties", {})
    conn2 = csc.Connection._from_dict(
        title=title,
        ConnectionName=props.get("ConnectionName"),
        ProviderType=props.get("ProviderType")
    )
    
    # Compare the dictionaries
    assert conn1.to_dict() == conn2.to_dict()


@given(title=valid_title_strategy,
       connection_name=simple_string_strategy)
def test_connection_json_serialization(title, connection_name):
    """Test that Connection objects can be serialized to JSON and parsed back"""
    conn = csc.Connection(
        title=title,
        ConnectionName=connection_name
    )
    
    # Serialize to JSON and parse back
    json_str = conn.to_json()
    parsed = json.loads(json_str)
    
    # Should be a valid dictionary
    assert isinstance(parsed, dict)
    assert "Type" in parsed
    assert parsed["Type"] == "AWS::CodeStarConnections::Connection"
    assert "Properties" in parsed
    assert parsed["Properties"]["ConnectionName"] == connection_name


@given(invalid_provider=invalid_provider_type_strategy)
def test_connection_invalid_provider_type_validation(invalid_provider):
    """Test that invalid provider types are rejected by the validator"""
    from troposphere.validators.codestarconnections import validate_connection_providertype
    
    try:
        validate_connection_providertype(invalid_provider)
        # If we get here, validation passed when it shouldn't have
        assert False, f"Validator should have rejected '{invalid_provider}'"
    except ValueError as e:
        # This is expected
        assert "Connection ProviderType must be one of:" in str(e)


@given(title=st.text(min_size=1).filter(lambda x: not re.match(r'^[a-zA-Z0-9]+$', x)))
def test_invalid_title_validation(title):
    """Test that non-alphanumeric titles are rejected"""
    try:
        conn = csc.Connection(
            title=title,
            ConnectionName="test"
        )
        # If we get here without exception, the title was accepted
        # Check if it's actually invalid
        if not re.match(r'^[a-zA-Z0-9]+$', title):
            assert False, f"Title '{title}' should have been rejected"
    except ValueError as e:
        assert 'not alphanumeric' in str(e)


@given(title=valid_title_strategy,
       connection_arn=arn_strategy,
       owner_id=simple_string_strategy,
       repo_name=simple_string_strategy)
def test_repository_link_creation_and_serialization(title, connection_arn, owner_id, repo_name):
    """Test RepositoryLink creation and JSON serialization"""
    repo_link = csc.RepositoryLink(
        title=title,
        ConnectionArn=connection_arn,
        OwnerId=owner_id,
        RepositoryName=repo_name
    )
    
    # Test serialization
    json_str = repo_link.to_json()
    parsed = json.loads(json_str)
    
    assert parsed["Type"] == "AWS::CodeStarConnections::RepositoryLink"
    assert parsed["Properties"]["ConnectionArn"] == connection_arn
    assert parsed["Properties"]["OwnerId"] == owner_id
    assert parsed["Properties"]["RepositoryName"] == repo_name


@given(title=valid_title_strategy,
       branch=simple_string_strategy,
       config_file=simple_string_strategy,
       repo_link_id=simple_string_strategy,
       resource_name=simple_string_strategy,
       role_arn=arn_strategy,
       sync_type=st.sampled_from(["CFN_STACK_SYNC"]))
def test_sync_configuration_roundtrip(title, branch, config_file, repo_link_id, resource_name, role_arn, sync_type):
    """Test SyncConfiguration dict roundtrip"""
    sync1 = csc.SyncConfiguration(
        title=title,
        Branch=branch,
        ConfigFile=config_file,
        RepositoryLinkId=repo_link_id,
        ResourceName=resource_name,
        RoleArn=role_arn,
        SyncType=sync_type
    )
    
    # Convert to dict
    sync_dict = sync1.to_dict()
    props = sync_dict.get("Properties", {})
    
    # Create from dict
    sync2 = csc.SyncConfiguration._from_dict(
        title=title,
        Branch=props.get("Branch"),
        ConfigFile=props.get("ConfigFile"),
        RepositoryLinkId=props.get("RepositoryLinkId"),
        ResourceName=props.get("ResourceName"),
        RoleArn=props.get("RoleArn"),
        SyncType=props.get("SyncType")
    )
    
    assert sync1.to_dict() == sync2.to_dict()


@given(title=valid_title_strategy)
def test_connection_missing_required_property(title):
    """Test that Connection fails without required ConnectionName"""
    try:
        # Try creating without required ConnectionName
        conn = csc.Connection(title=title)
        # Now try to convert to dict which should trigger validation
        conn.to_dict()
        assert False, "Should have raised error for missing required property"
    except TypeError:
        # This is expected for missing required argument in constructor
        pass


@given(title=valid_title_strategy,
       connection_name=simple_string_strategy,
       tag_key=simple_string_strategy,
       tag_value=simple_string_strategy)
def test_connection_with_tags(title, connection_name, tag_key, tag_value):
    """Test that Connection handles Tags properly"""
    # Create connection with tags
    conn = csc.Connection(
        title=title,
        ConnectionName=connection_name,
        Tags=Tags({tag_key: tag_value})
    )
    
    # Serialize and check
    conn_dict = conn.to_dict()
    assert "Properties" in conn_dict
    assert "Tags" in conn_dict["Properties"]
    
    # Tags should be a list of key-value pairs
    tags = conn_dict["Properties"]["Tags"]
    assert isinstance(tags, list)
    assert len(tags) == 1
    assert tags[0]["Key"] == tag_key
    assert tags[0]["Value"] == tag_value


@given(provider_type=provider_type_strategy)
def test_validate_connection_providertype_accepts_valid(provider_type):
    """Test that the validator accepts all valid provider types"""
    from troposphere.validators.codestarconnections import validate_connection_providertype
    
    result = validate_connection_providertype(provider_type)
    assert result == provider_type