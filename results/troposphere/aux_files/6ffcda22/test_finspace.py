#!/usr/bin/env python
"""Property-based tests for troposphere.finspace module"""

import sys
import os
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import troposphere.finspace as finspace
from troposphere import Template
import json


# Strategy for valid CloudFormation resource titles (alphanumeric only)
valid_titles = st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')), min_size=1, max_size=255)

# Strategy for invalid titles (containing non-alphanumeric characters)
invalid_titles = st.text(min_size=1, max_size=255).filter(
    lambda s: not s.isalnum() or s == ""
)

# Strategy for email addresses
email_strategy = st.text(min_size=1, max_size=50).map(lambda s: f"{s}@example.com")

# Strategy for names
name_strategy = st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll')), min_size=1, max_size=50)

# Strategy for URLs
url_strategy = st.text(min_size=1, max_size=100).map(lambda s: f"https://example.com/{s}")


@given(valid_titles)
def test_environment_valid_title_accepted(title):
    """Test that Environment accepts valid alphanumeric titles"""
    env = finspace.Environment(title, Name="TestEnvironment")
    assert env.title == title


@given(invalid_titles)
def test_environment_invalid_title_rejected(title):
    """Test that Environment rejects non-alphanumeric titles"""
    try:
        env = finspace.Environment(title, Name="TestEnvironment")
        # If we get here, the title was accepted but shouldn't have been
        # Check if it's actually invalid
        import re
        valid_names = re.compile(r"^[a-zA-Z0-9]+$")
        if not valid_names.match(title):
            # This is a bug - invalid title was accepted
            assert False, f"Invalid title '{title}' was accepted but should have been rejected"
    except ValueError as e:
        # Expected behavior - invalid titles should raise ValueError
        assert 'not alphanumeric' in str(e)


@given(valid_titles, name_strategy)
def test_environment_required_property(title, name):
    """Test that Environment requires Name property"""
    # Test that Name is required
    try:
        env = finspace.Environment(title)
        # Try to convert to dict which should trigger validation
        env.to_dict()
        assert False, "Environment should require Name property"
    except ValueError as e:
        assert "required" in str(e).lower()
    
    # Test that it works with Name provided
    env = finspace.Environment(title, Name=name)
    d = env.to_dict()
    assert d['Properties']['Name'] == name


@given(valid_titles, name_strategy, st.one_of(st.none(), st.text(max_size=100)))
def test_environment_optional_properties(title, name, description):
    """Test that optional properties work correctly"""
    kwargs = {'Name': name}
    if description is not None:
        kwargs['Description'] = description
    
    env = finspace.Environment(title, **kwargs)
    d = env.to_dict()
    
    assert d['Properties']['Name'] == name
    if description is not None:
        assert d['Properties']['Description'] == description
    else:
        assert 'Description' not in d['Properties']


@given(
    valid_titles,
    name_strategy,
    email_strategy,
    name_strategy,
    name_strategy
)
def test_superuser_parameters(title, env_name, email, first_name, last_name):
    """Test SuperuserParameters property"""
    superuser = finspace.SuperuserParameters(
        EmailAddress=email,
        FirstName=first_name,
        LastName=last_name
    )
    
    env = finspace.Environment(
        title,
        Name=env_name,
        SuperuserParameters=superuser
    )
    
    d = env.to_dict()
    assert d['Properties']['SuperuserParameters']['EmailAddress'] == email
    assert d['Properties']['SuperuserParameters']['FirstName'] == first_name
    assert d['Properties']['SuperuserParameters']['LastName'] == last_name


@given(
    valid_titles,
    name_strategy,
    st.one_of(st.none(), st.text(max_size=100)),
    st.one_of(st.none(), st.text(max_size=50))
)
def test_environment_round_trip(title, name, description, kms_key):
    """Test that Environment can round-trip through to_dict/from_dict"""
    kwargs = {'Name': name}
    if description is not None:
        kwargs['Description'] = description
    if kms_key is not None:
        kwargs['KmsKeyId'] = kms_key
    
    env1 = finspace.Environment(title, **kwargs)
    dict1 = env1.to_dict()
    
    # Extract just the Properties for from_dict
    props = dict1.get('Properties', {})
    env2 = finspace.Environment.from_dict(title, props)
    dict2 = env2.to_dict()
    
    assert dict1 == dict2


@given(
    valid_titles, 
    name_strategy,
    st.lists(st.tuples(st.text(min_size=1, max_size=50), st.text(min_size=1, max_size=100)), max_size=5)
)
def test_attribute_map_items(title, env_name, attr_items):
    """Test AttributeMapItems in FederationParameters"""
    if not attr_items:
        return  # Skip empty lists
    
    attribute_map = [
        finspace.AttributeMapItems(Key=k, Value=v) 
        for k, v in attr_items
    ]
    
    fed_params = finspace.FederationParameters(
        AttributeMap=attribute_map
    )
    
    env = finspace.Environment(
        title,
        Name=env_name,
        FederationParameters=fed_params
    )
    
    d = env.to_dict()
    assert 'FederationParameters' in d['Properties']
    assert 'AttributeMap' in d['Properties']['FederationParameters']
    assert len(d['Properties']['FederationParameters']['AttributeMap']) == len(attr_items)
    
    for i, (key, value) in enumerate(attr_items):
        assert d['Properties']['FederationParameters']['AttributeMap'][i]['Key'] == key
        assert d['Properties']['FederationParameters']['AttributeMap'][i]['Value'] == value


@given(valid_titles, name_strategy)
def test_environment_equality(title, name):
    """Test that two Environment objects with same properties are equal"""
    env1 = finspace.Environment(title, Name=name)
    env2 = finspace.Environment(title, Name=name)
    
    assert env1 == env2
    assert not (env1 != env2)


@given(valid_titles, name_strategy, st.text(min_size=1, max_size=100))
def test_environment_inequality(title, name1, name2):
    """Test that Environment objects with different properties are not equal"""
    assume(name1 != name2)
    
    env1 = finspace.Environment(title, Name=name1)
    env2 = finspace.Environment(title, Name=name2)
    
    assert env1 != env2
    assert not (env1 == env2)


@given(valid_titles, name_strategy)
def test_environment_hash_consistency(title, name):
    """Test that equal Environment objects have the same hash"""
    env1 = finspace.Environment(title, Name=name)
    env2 = finspace.Environment(title, Name=name)
    
    assert env1 == env2
    assert hash(env1) == hash(env2)


@given(
    valid_titles,
    name_strategy, 
    st.one_of(st.none(), st.sampled_from(['FEDERATED', 'LOCAL']))
)
def test_federation_mode(title, name, fed_mode):
    """Test FederationMode property accepts valid values"""
    kwargs = {'Name': name}
    if fed_mode is not None:
        kwargs['FederationMode'] = fed_mode
    
    env = finspace.Environment(title, **kwargs)
    d = env.to_dict()
    
    if fed_mode is not None:
        assert d['Properties']['FederationMode'] == fed_mode
    else:
        assert 'FederationMode' not in d['Properties']


@given(valid_titles, name_strategy, st.text(min_size=1, max_size=2000))
def test_large_saml_document(title, name, saml_doc):
    """Test that FederationParameters can handle large SAML documents"""
    fed_params = finspace.FederationParameters(
        SamlMetadataDocument=saml_doc
    )
    
    env = finspace.Environment(
        title,
        Name=name,
        FederationParameters=fed_params
    )
    
    d = env.to_dict()
    assert d['Properties']['FederationParameters']['SamlMetadataDocument'] == saml_doc


@given(valid_titles, name_strategy)
def test_template_integration(title, name):
    """Test that Environment integrates correctly with Template"""
    template = Template()
    env = finspace.Environment(title, Name=name, template=template)
    
    # Check that the resource was added to the template
    template_dict = template.to_dict()
    assert 'Resources' in template_dict
    assert title in template_dict['Resources']
    assert template_dict['Resources'][title]['Type'] == 'AWS::FinSpace::Environment'
    assert template_dict['Resources'][title]['Properties']['Name'] == name


@given(
    st.text(min_size=1, max_size=100),
    st.text(min_size=1, max_size=100)
)
def test_attribute_map_no_validation(key, value):
    """Test that AttributeMapItems accepts any string key/value pairs"""
    # AttributeMapItems should accept any strings without validation
    attr = finspace.AttributeMapItems(Key=key, Value=value)
    d = attr.to_dict()
    assert d['Key'] == key
    assert d['Value'] == value


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])