#!/usr/bin/env python3
"""Property-based tests for troposphere.codeconnections module"""

import json
import re
import sys
import os

# Add the virtual env to path
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import pytest

from troposphere import Tags
from troposphere.codeconnections import Connection


# Strategy for valid alphanumeric titles (CloudFormation requirement)
valid_title_strategy = st.text(
    alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')),
    min_size=1,
    max_size=255
).filter(lambda x: re.match(r'^[a-zA-Z0-9]+$', x))

# Strategy for string values that could be ARNs or names
string_value_strategy = st.text(min_size=0, max_size=1024)

# Strategy for tag keys and values
tag_key_strategy = st.text(min_size=1, max_size=128).filter(lambda x: x.strip() != '')
tag_value_strategy = st.text(min_size=0, max_size=256)

# Strategy for a Tags object
tags_strategy = st.dictionaries(
    keys=tag_key_strategy,
    values=tag_value_strategy,
    min_size=0,
    max_size=50
).map(lambda d: Tags(**d) if d else None)


@given(
    title=valid_title_strategy,
    connection_name=string_value_strategy,
    host_arn=st.one_of(st.none(), string_value_strategy),
    provider_type=st.one_of(st.none(), string_value_strategy),
    tags=tags_strategy
)
def test_connection_round_trip(title, connection_name, host_arn, provider_type, tags):
    """Test that from_dict(to_dict(connection)) equals the original connection"""
    
    # Create a Connection object
    kwargs = {'ConnectionName': connection_name}
    if host_arn is not None:
        kwargs['HostArn'] = host_arn
    if provider_type is not None:
        kwargs['ProviderType'] = provider_type
    if tags is not None:
        kwargs['Tags'] = tags
    
    original = Connection(title, **kwargs)
    
    # Convert to dict and back
    as_dict = original.to_dict()
    
    # Extract the Properties from the dict for from_dict
    properties = as_dict.get('Properties', {})
    reconstructed = Connection.from_dict(title, properties)
    
    # They should be equal
    assert original == reconstructed
    assert original.title == reconstructed.title
    assert original.to_json(validation=False) == reconstructed.to_json(validation=False)


@given(
    title=valid_title_strategy,
    host_arn=st.one_of(st.none(), string_value_strategy),
    provider_type=st.one_of(st.none(), string_value_strategy),
    tags=tags_strategy
)
def test_connection_required_property_validation(title, host_arn, provider_type, tags):
    """Test that Connection raises error when required ConnectionName is missing"""
    
    kwargs = {}
    if host_arn is not None:
        kwargs['HostArn'] = host_arn
    if provider_type is not None:
        kwargs['ProviderType'] = provider_type
    if tags is not None:
        kwargs['Tags'] = tags
    
    # Create without the required ConnectionName
    conn = Connection(title, **kwargs)
    
    # Validation should fail when converting to dict
    with pytest.raises(ValueError, match=".*ConnectionName.*required.*"):
        conn.to_dict()


@given(
    invalid_title=st.text(min_size=1, max_size=255).filter(
        lambda x: not re.match(r'^[a-zA-Z0-9]+$', x)
    ),
    connection_name=string_value_strategy
)
def test_connection_title_validation(invalid_title, connection_name):
    """Test that Connection validates title to be alphanumeric"""
    
    # Create a connection with invalid title
    conn = Connection(invalid_title, ConnectionName=connection_name)
    
    # Title validation should fail
    with pytest.raises(ValueError, match='Name.*not alphanumeric'):
        conn.validate_title()


@given(
    tags1=st.dictionaries(
        keys=tag_key_strategy,
        values=tag_value_strategy,
        min_size=0,
        max_size=25
    ),
    tags2=st.dictionaries(
        keys=tag_key_strategy,
        values=tag_value_strategy,
        min_size=0,
        max_size=25
    )
)
def test_tags_concatenation(tags1, tags2):
    """Test that Tags concatenation with + operator works correctly"""
    
    t1 = Tags(**tags1)
    t2 = Tags(**tags2)
    
    # Concatenate tags
    combined = t1 + t2
    
    # Check that all tags are present
    combined_dict = combined.to_dict()
    
    # Convert original tags to dict format for comparison
    t1_dict = t1.to_dict()
    t2_dict = t2.to_dict()
    
    # All tags from both should be in combined (t1 first, then t2)
    assert len(combined_dict) == len(t1_dict) + len(t2_dict)
    
    # First tags should match t1
    for i, tag in enumerate(t1_dict):
        assert combined_dict[i] == tag
    
    # Remaining tags should match t2
    for i, tag in enumerate(t2_dict):
        assert combined_dict[len(t1_dict) + i] == tag


@given(
    title=valid_title_strategy,
    bad_connection_name=st.one_of(
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.lists(st.text()),
        st.dictionaries(st.text(), st.text())
    )
)
def test_connection_type_validation(title, bad_connection_name):
    """Test that Connection validates property types correctly"""
    
    # Try to create Connection with non-string ConnectionName
    conn = Connection(title)
    
    # Type validation should fail when setting invalid type
    with pytest.raises(TypeError, match=".*ConnectionName.*expected.*str"):
        conn.ConnectionName = bad_connection_name


@given(
    title=valid_title_strategy,
    connection_name=string_value_strategy,
    bad_tags=st.one_of(
        st.text(),  # String instead of Tags object
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.lists(st.text()).filter(lambda x: len(x) > 0)  # Non-empty list of strings
    )
)
def test_connection_tags_type_validation(title, connection_name, bad_tags):
    """Test that Connection validates Tags property type correctly"""
    
    conn = Connection(title, ConnectionName=connection_name)
    
    # Setting invalid Tags type should raise TypeError
    with pytest.raises(TypeError):
        conn.Tags = bad_tags


@given(
    title=valid_title_strategy,
    data=st.data()
)
def test_connection_properties_preservation(title, data):
    """Test that all set properties are preserved correctly"""
    
    # Generate random property values
    connection_name = data.draw(string_value_strategy)
    host_arn = data.draw(st.one_of(st.none(), string_value_strategy))
    provider_type = data.draw(st.one_of(st.none(), string_value_strategy))
    tags = data.draw(tags_strategy)
    
    kwargs = {'ConnectionName': connection_name}
    if host_arn is not None:
        kwargs['HostArn'] = host_arn
    if provider_type is not None:
        kwargs['ProviderType'] = provider_type
    if tags is not None:
        kwargs['Tags'] = tags
    
    conn = Connection(title, **kwargs)
    
    # Check all properties are preserved
    assert conn.ConnectionName == connection_name
    if host_arn is not None:
        assert conn.HostArn == host_arn
    if provider_type is not None:
        assert conn.ProviderType == provider_type
    if tags is not None:
        assert conn.Tags == tags
    
    # Check they're in the dict representation
    conn_dict = conn.to_dict()
    props = conn_dict.get('Properties', {})
    assert props.get('ConnectionName') == connection_name
    if host_arn is not None:
        assert props.get('HostArn') == host_arn
    if provider_type is not None:
        assert props.get('ProviderType') == provider_type


@given(
    tag_dict=st.dictionaries(
        keys=st.one_of(
            tag_key_strategy,  # String keys
            st.integers(),  # Integer keys
            st.tuples(st.text(), st.text())  # Tuple keys (non-sortable)
        ),
        values=tag_value_strategy,
        min_size=1,
        max_size=10
    )
)
def test_tags_handles_non_string_keys(tag_dict):
    """Test that Tags handles non-string keys without crashing"""
    
    # This should not raise an exception even with non-string keys
    tags = Tags(**tag_dict)
    
    # Should be able to convert to dict
    tags_list = tags.to_dict()
    
    # All keys should be present
    assert len(tags_list) == len(tag_dict)
    
    # All key-value pairs should be represented
    for tag in tags_list:
        assert 'Key' in tag
        assert 'Value' in tag


if __name__ == '__main__':
    pytest.main([__file__, '-v'])