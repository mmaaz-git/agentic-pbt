#!/usr/bin/env python3
"""Test for potential hash/equality bug in troposphere"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, settings
import troposphere.opsworkscm as opsworkscm
import json


# Looking at the code, I noticed a potential issue with __eq__ and __hash__:
# - __eq__ compares using to_json() which doesn't include the title
# - __hash__ explicitly adds the title to the dict before hashing
# This could lead to objects being equal but having different hashes

@given(
    title=st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=50),
    name_attr=st.text(min_size=0, max_size=100),
    value_attr=st.text(min_size=0, max_size=100)
)
@settings(max_examples=1000)
def test_engine_attribute_hash_equality_consistency(title, name_attr, value_attr):
    """Test that if two EngineAttribute objects are equal, they have the same hash"""
    
    # Create two identical EngineAttribute objects with different titles
    # EngineAttribute doesn't require a title in __init__
    ea1 = opsworkscm.EngineAttribute(title=None, Name=name_attr, Value=value_attr)
    ea2 = opsworkscm.EngineAttribute(title=None, Name=name_attr, Value=value_attr)
    
    # According to Python's data model, if a == b, then hash(a) == hash(b)
    if ea1 == ea2:
        assert hash(ea1) == hash(ea2), f"Equal objects must have equal hashes! hash(ea1)={hash(ea1)}, hash(ea2)={hash(ea2)}"
    
    # Also test with actual titles
    ea3 = opsworkscm.EngineAttribute(title=title, Name=name_attr, Value=value_attr)
    ea4 = opsworkscm.EngineAttribute(title=title, Name=name_attr, Value=value_attr)
    
    if ea3 == ea4:
        assert hash(ea3) == hash(ea4), f"Equal objects with titles must have equal hashes!"


@given(
    common_props=st.fixed_dictionaries({
        'InstanceProfileArn': st.text(min_size=1, max_size=100),
        'InstanceType': st.text(min_size=1, max_size=50),
        'ServiceRoleArn': st.text(min_size=1, max_size=100),
    }),
    title1=st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=50),
    title2=st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=50),
)
@settings(max_examples=500)
def test_server_different_titles_not_equal(common_props, title1, title2):
    """Test that servers with different titles but same properties are handled correctly"""
    
    # Create two servers with same properties but potentially different titles
    server1 = opsworkscm.Server(title1, **common_props)
    server2 = opsworkscm.Server(title2, **common_props)
    
    # According to the __eq__ implementation, title is part of equality
    if title1 != title2:
        assert server1 != server2, "Servers with different titles should not be equal"
        # And they should have different hashes
        assert hash(server1) != hash(server2), "Servers with different titles should have different hashes"
    else:
        assert server1 == server2, "Servers with same title and properties should be equal"
        assert hash(server1) == hash(server2), "Equal servers must have equal hashes"


@given(
    props=st.fixed_dictionaries({
        'Name': st.text(min_size=0, max_size=100),
        'Value': st.text(min_size=0, max_size=100)
    })
)
@settings(max_examples=500)
def test_engine_attribute_from_dict_preserves_equality(props):
    """Test that from_dict creates an object equal to the original"""
    
    # Create original
    original = opsworkscm.EngineAttribute(**props)
    
    # Convert to dict and back
    as_dict = original.to_dict()
    restored = opsworkscm.EngineAttribute.from_dict(None, as_dict)
    
    # They should be equal
    assert original == restored, f"Round-trip through dict should preserve equality"
    
    # And have the same hash
    assert hash(original) == hash(restored), f"Round-trip should preserve hash"
    
    # And produce the same dict
    assert original.to_dict() == restored.to_dict(), f"Round-trip should produce identical dicts"


if __name__ == "__main__":
    print("Testing for hash/equality consistency bugs...")
    test_engine_attribute_hash_equality_consistency()
    test_server_different_titles_not_equal()
    test_engine_attribute_from_dict_preserves_equality()
    print("Tests completed!")