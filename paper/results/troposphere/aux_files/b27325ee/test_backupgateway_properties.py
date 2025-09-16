"""Property-based tests for troposphere.backupgateway module"""

import re
from hypothesis import given, assume, strategies as st, settings
from troposphere import backupgateway, Tags
import json


# Strategy for valid CloudFormation resource names (alphanumeric only)
valid_cfn_names = st.text(alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")), min_size=1, max_size=255)

# Strategy for string property values
string_values = st.text(min_size=0, max_size=1000)

# Strategy for KMS key ARNs
kms_key_arns = st.one_of(
    st.none(),
    st.text(min_size=1).map(lambda s: f"arn:aws:kms:us-east-1:123456789012:key/{s}")
)

# Strategy for log group ARNs  
log_group_arns = st.one_of(
    st.none(),
    st.text(min_size=1).map(lambda s: f"arn:aws:logs:us-east-1:123456789012:log-group:{s}")
)

# Strategy for generating Tags
tag_strategy = st.dictionaries(
    keys=st.text(min_size=1, max_size=127),
    values=st.text(min_size=0, max_size=255),
    min_size=0,
    max_size=50
)


@given(
    title=valid_cfn_names,
    host=st.one_of(st.none(), string_values),
    kms_key_arn=st.one_of(st.none(), string_values),
    log_group_arn=st.one_of(st.none(), string_values),
    name=st.one_of(st.none(), string_values),
    password=st.one_of(st.none(), string_values),
    username=st.one_of(st.none(), string_values),
    tags=st.one_of(st.none(), tag_strategy)
)
def test_round_trip_property(title, host, kms_key_arn, log_group_arn, name, password, username, tags):
    """Test that Hypervisor objects can round-trip through dict representation"""
    
    # Create hypervisor with properties
    h1 = backupgateway.Hypervisor(title)
    
    # Set properties if not None
    if host is not None:
        h1.Host = host
    if kms_key_arn is not None:
        h1.KmsKeyArn = kms_key_arn
    if log_group_arn is not None:
        h1.LogGroupArn = log_group_arn
    if name is not None:
        h1.Name = name
    if password is not None:
        h1.Password = password
    if username is not None:
        h1.Username = username
    if tags is not None:
        h1.Tags = Tags(**tags)
    
    # Convert to dict
    dict1 = h1.to_dict()
    
    # Extract properties for round-trip
    props = dict1.get('Properties', {})
    
    # Create new object from dict
    h2 = backupgateway.Hypervisor._from_dict(title, **props)
    
    # Convert back to dict
    dict2 = h2.to_dict()
    
    # They should be equal
    assert dict1 == dict2, f"Round-trip failed: {dict1} != {dict2}"


@given(
    title=valid_cfn_names,
    properties=st.dictionaries(
        keys=st.sampled_from(['Host', 'KmsKeyArn', 'LogGroupArn', 'Name', 'Password', 'Username']),
        values=string_values,
        min_size=0,
        max_size=6
    )
)
def test_properties_preservation(title, properties):
    """Test that all set properties appear in to_dict() output"""
    
    h = backupgateway.Hypervisor(title)
    
    # Set all properties
    for prop_name, prop_value in properties.items():
        setattr(h, prop_name, prop_value)
    
    # Get dict representation
    result = h.to_dict()
    
    # Check that all properties are preserved
    if properties:
        assert 'Properties' in result
        for prop_name, prop_value in properties.items():
            assert prop_name in result['Properties']
            assert result['Properties'][prop_name] == prop_value
    
    # Type should always be present
    assert result['Type'] == 'AWS::BackupGateway::Hypervisor'


@given(
    title=valid_cfn_names,
    invalid_value=st.one_of(
        st.integers(),
        st.floats(),
        st.lists(st.integers()),
        st.dictionaries(st.text(), st.text()),
        st.booleans()
    )
)
def test_type_validation(title, invalid_value):
    """Test that setting properties to wrong types raises TypeError"""
    
    h = backupgateway.Hypervisor(title)
    
    # All these properties expect strings
    string_properties = ['Host', 'KmsKeyArn', 'LogGroupArn', 'Name', 'Password', 'Username']
    
    for prop in string_properties:
        try:
            setattr(h, prop, invalid_value)
            # If we get here without exception, that's a bug
            # unless the value happens to be coercible to string
            value = getattr(h, prop)
            # Check if it was coerced
            if not isinstance(value, str):
                assert False, f"Property {prop} accepted non-string value {invalid_value} without coercion"
        except TypeError as e:
            # This is expected for non-string values
            assert prop in str(e)
            assert "expected <class 'str'>" in str(e) or "expected (<class 'str'>," in str(e)


@given(title=st.text(min_size=1))
def test_title_validation(title):
    """Test that title must be alphanumeric"""
    
    # Check if title is valid (alphanumeric only)
    is_valid = bool(re.match(r'^[a-zA-Z0-9]+$', title))
    
    try:
        h = backupgateway.Hypervisor(title)
        h.validate_title()
        # If we get here, title should be valid
        assert is_valid, f"Invalid title '{title}' was accepted"
    except ValueError as e:
        # If we get an error, title should be invalid
        assert not is_valid, f"Valid title '{title}' was rejected: {e}"
        assert 'not alphanumeric' in str(e)


@given(
    title=valid_cfn_names,
    properties=st.dictionaries(
        keys=st.sampled_from(['Host', 'KmsKeyArn', 'LogGroupArn', 'Name', 'Password', 'Username']),
        values=string_values,
        min_size=1,
        max_size=6
    )
)
def test_json_serialization(title, properties):
    """Test that Hypervisor objects can be serialized to valid JSON"""
    
    h = backupgateway.Hypervisor(title)
    
    # Set properties
    for prop_name, prop_value in properties.items():
        setattr(h, prop_name, prop_value)
    
    # Convert to JSON
    json_str = h.to_json()
    
    # Should be valid JSON
    parsed = json.loads(json_str)
    
    # Should contain the same data as to_dict()
    assert parsed == h.to_dict()


@given(
    title=valid_cfn_names,
    host=st.one_of(st.none(), string_values),
    name=st.one_of(st.none(), string_values)
)
@settings(max_examples=1000)
def test_property_independence(title, host, name):
    """Test that properties can be set independently without affecting each other"""
    
    h = backupgateway.Hypervisor(title)
    
    # Set properties in different orders and verify independence
    if host is not None:
        h.Host = host
    
    if name is not None:
        h.Name = name
        
    result = h.to_dict()
    
    # Create another with reversed order
    h2 = backupgateway.Hypervisor(title)
    
    if name is not None:
        h2.Name = name
        
    if host is not None:
        h2.Host = host
    
    result2 = h2.to_dict()
    
    # Results should be identical regardless of order
    assert result == result2


@given(
    title1=valid_cfn_names,
    title2=valid_cfn_names,
    shared_props=st.dictionaries(
        keys=st.sampled_from(['Host', 'Name', 'Username']),
        values=string_values,
        min_size=0,
        max_size=3
    )
)
def test_multiple_instances_independence(title1, title2, shared_props):
    """Test that multiple Hypervisor instances don't interfere with each other"""
    
    assume(title1 != title2)  # Ensure different titles
    
    h1 = backupgateway.Hypervisor(title1)
    h2 = backupgateway.Hypervisor(title2)
    
    # Set same properties on both
    for prop_name, prop_value in shared_props.items():
        setattr(h1, prop_name, prop_value)
        setattr(h2, prop_name, prop_value + "_modified")
    
    dict1 = h1.to_dict()
    dict2 = h2.to_dict()
    
    # They should have different values
    if shared_props:
        for prop_name in shared_props:
            assert dict1['Properties'][prop_name] != dict2['Properties'][prop_name]
    
    # But same type
    assert dict1['Type'] == dict2['Type'] == 'AWS::BackupGateway::Hypervisor'