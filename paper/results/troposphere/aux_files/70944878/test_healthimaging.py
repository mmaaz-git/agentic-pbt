#!/usr/bin/env python3
"""Property-based tests for troposphere.healthimaging module"""

import json
import string
import sys
import os

# Add the virtualenv site-packages to path
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, assume, strategies as st, settings
from hypothesis.strategies import composite
import troposphere.healthimaging as healthimaging


# Strategy for valid alphanumeric titles (as required by troposphere)
valid_titles = st.text(
    alphabet=string.ascii_letters + string.digits, 
    min_size=1, 
    max_size=255
)

# Strategy for invalid titles with special characters
invalid_titles = st.one_of(
    st.text(min_size=1).filter(lambda x: not x.replace(' ', '').isalnum()),
    st.text(alphabet=' !@#$%^&*()-=+[]{}|;:,.<>?/', min_size=1),
    st.just(''),  # empty string
)

# Strategy for valid KMS key ARNs
kms_arns = st.text(min_size=1, max_size=100).map(
    lambda x: f"arn:aws:kms:us-east-1:123456789012:key/{x}"
)

# Strategy for datastore names  
datastore_names = st.text(min_size=1, max_size=100)

# Strategy for valid tags
tags_dict = st.dictionaries(
    keys=st.text(min_size=1, max_size=50),
    values=st.text(min_size=0, max_size=100),
    min_size=0,
    max_size=10
)


@given(valid_titles)
def test_valid_title_accepted(title):
    """Valid alphanumeric titles should be accepted"""
    ds = healthimaging.Datastore(title)
    assert ds.title == title


@given(invalid_titles)
def test_invalid_title_rejected(title):
    """Non-alphanumeric titles should raise ValueError"""
    try:
        healthimaging.Datastore(title)
        # If we get here, the title was accepted when it shouldn't have been
        assert False, f"Title '{title}' should have been rejected but was accepted"
    except ValueError as e:
        # This is expected - invalid titles should raise ValueError
        assert 'not alphanumeric' in str(e) or title == ''


@given(valid_titles, datastore_names, kms_arns, tags_dict)
def test_property_setting_and_retrieval(title, name, arn, tags):
    """Properties set on Datastore should be retrievable"""
    ds = healthimaging.Datastore(
        title,
        DatastoreName=name,
        KmsKeyArn=arn,
        Tags=tags
    )
    assert ds.DatastoreName == name
    assert ds.KmsKeyArn == arn
    assert ds.Tags == tags


@given(valid_titles)
def test_type_validation_datastore_name(title):
    """DatastoreName must be a string, not other types"""
    ds = healthimaging.Datastore(title)
    
    # These should work (strings)
    ds.DatastoreName = "valid-name"
    assert ds.DatastoreName == "valid-name"
    
    # These should fail (non-strings)
    try:
        ds.DatastoreName = 123
        assert False, "Should have raised TypeError for integer"
    except TypeError:
        pass  # Expected
        
    try:
        ds.DatastoreName = ["list", "value"]
        assert False, "Should have raised TypeError for list"
    except TypeError:
        pass  # Expected


@given(valid_titles, datastore_names, kms_arns, tags_dict)
def test_to_dict_structure(title, name, arn, tags):
    """to_dict() should produce expected CloudFormation structure"""
    ds = healthimaging.Datastore(
        title,
        DatastoreName=name,
        KmsKeyArn=arn,
        Tags=tags
    )
    
    result = ds.to_dict()
    
    # Should have Type and Properties keys
    assert 'Type' in result
    assert result['Type'] == 'AWS::HealthImaging::Datastore'
    assert 'Properties' in result
    
    # Properties should contain our values
    props = result['Properties']
    assert props['DatastoreName'] == name
    assert props['KmsKeyArn'] == arn
    assert props['Tags'] == tags


@given(valid_titles, datastore_names, kms_arns, tags_dict)
def test_json_serialization_valid(title, name, arn, tags):
    """to_json() should produce valid JSON that can be parsed"""
    ds = healthimaging.Datastore(
        title,
        DatastoreName=name,
        KmsKeyArn=arn,
        Tags=tags
    )
    
    json_str = ds.to_json()
    
    # Should be valid JSON
    try:
        parsed = json.loads(json_str)
    except json.JSONDecodeError:
        assert False, f"Invalid JSON produced: {json_str}"
    
    # Parsed JSON should match to_dict()
    assert parsed == ds.to_dict()


@given(valid_titles, datastore_names, kms_arns, tags_dict)  
def test_from_dict_round_trip(title, name, arn, tags):
    """from_dict(to_dict()) should preserve the object"""
    ds1 = healthimaging.Datastore(
        title,
        DatastoreName=name,
        KmsKeyArn=arn,
        Tags=tags
    )
    
    # Convert to dict
    dict_repr = ds1.to_dict()
    
    # Extract properties for from_dict (it doesn't expect Type key)
    props = dict_repr.get('Properties', {})
    
    # Create new object from dict
    ds2 = healthimaging.Datastore._from_dict(title, **props)
    
    # Properties should match
    assert ds2.DatastoreName == ds1.DatastoreName
    assert ds2.KmsKeyArn == ds1.KmsKeyArn
    assert ds2.Tags == ds1.Tags
    assert ds2.title == ds1.title


@given(valid_titles, datastore_names)
def test_equality_same_properties(title, name):
    """Two Datastore objects with same properties should be equal"""
    ds1 = healthimaging.Datastore(title, DatastoreName=name)
    ds2 = healthimaging.Datastore(title, DatastoreName=name)
    
    assert ds1 == ds2
    assert not (ds1 != ds2)


@given(valid_titles, datastore_names, st.text(min_size=1, max_size=50))
def test_inequality_different_properties(title, name1, name2):
    """Two Datastore objects with different properties should not be equal"""
    assume(name1 != name2)  # Ensure names are different
    
    ds1 = healthimaging.Datastore(title, DatastoreName=name1)
    ds2 = healthimaging.Datastore(title, DatastoreName=name2)
    
    assert ds1 != ds2
    assert not (ds1 == ds2)


@given(valid_titles, st.text(min_size=1, max_size=50))
def test_inequality_different_titles(title1, title2):
    """Two Datastore objects with different titles should not be equal"""
    # Ensure both titles are valid and different
    assume(title2.replace(' ', '').isalnum() and title2)
    assume(title1 != title2)
    
    ds1 = healthimaging.Datastore(title1)
    ds2 = healthimaging.Datastore(title2)
    
    assert ds1 != ds2
    assert not (ds1 == ds2)


@given(valid_titles)
def test_ref_method(title):
    """ref() method should return a Ref object with the title"""
    ds = healthimaging.Datastore(title)
    ref = ds.ref()
    
    # Ref should be a troposphere Ref object pointing to our resource
    from troposphere import Ref
    assert isinstance(ref, Ref)
    assert ref.to_dict() == {'Ref': title}


@given(valid_titles, st.text(min_size=1, max_size=50))
def test_get_att_method(title, attribute):
    """get_att() method should return a GetAtt object"""
    ds = healthimaging.Datastore(title)
    getatt = ds.get_att(attribute)
    
    # GetAtt should be a troposphere GetAtt object
    from troposphere import GetAtt
    assert isinstance(getatt, GetAtt)
    assert getatt.to_dict() == {'Fn::GetAtt': [title, attribute]}