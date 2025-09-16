#!/usr/bin/env python3
"""Property-based tests for troposphere.codestarnotifications module"""

import sys
import json
from hypothesis import given, assume, strategies as st, settings
import pytest

# Add troposphere to path
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.codestarnotifications as csn
from troposphere import Tags


# Strategy for valid strings (AWS names/ARNs)
valid_string = st.text(min_size=1, max_size=255).filter(lambda x: x.strip())
valid_arn = st.text(min_size=20, max_size=500).filter(lambda x: x.strip() and not x.startswith(' '))
valid_name = st.text(alphabet=st.characters(min_codepoint=65, max_codepoint=122), min_size=1, max_size=64)

# Strategy for event type IDs
event_type_id = st.text(min_size=1, max_size=200)

# Strategy for detail types  
detail_type = st.sampled_from(["BASIC", "FULL"])

# Strategy for status
status = st.sampled_from(["ENABLED", "DISABLED"])

# Strategy for target types
target_type = st.sampled_from(["SNS", "AWSChatbotSlack"])


# Test 1: Target property validation and serialization
@given(address=valid_arn, t_type=target_type)
def test_target_roundtrip(address, t_type):
    """Test that Target can be created and serialized correctly"""
    target = csn.Target(TargetAddress=address, TargetType=t_type)
    
    # Check to_dict produces expected structure
    result = target.to_dict()
    assert result['TargetAddress'] == address
    assert result['TargetType'] == t_type
    
    # Check properties are accessible
    assert target.TargetAddress == address
    assert target.TargetType == t_type


# Test 2: Target requires both TargetAddress and TargetType
@given(address=valid_arn)
def test_target_missing_type_fails(address):
    """Test that Target fails without required TargetType property"""
    with pytest.raises((ValueError, TypeError)):
        target = csn.Target(TargetAddress=address)
        target.to_dict()  # Validation happens here


@given(t_type=target_type)
def test_target_missing_address_fails(t_type):
    """Test that Target fails without required TargetAddress property"""
    with pytest.raises((ValueError, TypeError)):
        target = csn.Target(TargetType=t_type)
        target.to_dict()  # Validation happens here


# Test 3: NotificationRule with all required properties
@given(
    name=valid_name,
    detail=detail_type,
    event_ids=st.lists(event_type_id, min_size=1, max_size=5),
    resource=valid_arn,
    target_addresses=st.lists(valid_arn, min_size=1, max_size=5),
    target_types=st.lists(target_type, min_size=1, max_size=5)
)
def test_notification_rule_creation(name, detail, event_ids, resource, target_addresses, target_types):
    """Test NotificationRule creation with required properties"""
    # Ensure we have same number of addresses and types for targets
    assume(len(target_addresses) == len(target_types))
    
    targets = [csn.Target(TargetAddress=addr, TargetType=ttype) 
               for addr, ttype in zip(target_addresses, target_types)]
    
    rule = csn.NotificationRule(
        "TestRule",
        Name=name,
        DetailType=detail,
        EventTypeIds=event_ids,
        Resource=resource,
        Targets=targets
    )
    
    result = rule.to_dict()
    assert result['Type'] == 'AWS::CodeStarNotifications::NotificationRule'
    assert result['Properties']['Name'] == name
    assert result['Properties']['DetailType'] == detail
    assert result['Properties']['EventTypeIds'] == event_ids
    assert result['Properties']['Resource'] == resource
    
    # Check targets are properly serialized
    result_targets = result['Properties']['Targets']
    assert len(result_targets) == len(targets)
    for i, target_dict in enumerate(result_targets):
        assert target_dict['TargetAddress'] == target_addresses[i]
        assert target_dict['TargetType'] == target_types[i]


# Test 4: NotificationRule missing required properties
@given(name=valid_name, detail=detail_type)
def test_notification_rule_missing_required_fails(name, detail):
    """Test that NotificationRule fails without all required properties"""
    with pytest.raises(ValueError):
        # Missing EventTypeIds, Resource, and Targets
        rule = csn.NotificationRule(
            "TestRule",
            Name=name,
            DetailType=detail
        )
        rule.to_dict()  # Validation happens here


# Test 5: JSON serialization invariant
@given(
    name=valid_name,
    detail=detail_type,
    event_ids=st.lists(event_type_id, min_size=1, max_size=3),
    resource=valid_arn,
    target_address=valid_arn,
    target_type=target_type
)
def test_json_serialization_invariant(name, detail, event_ids, resource, target_address, target_type):
    """Test that to_dict() output can be serialized to JSON and back"""
    target = csn.Target(TargetAddress=target_address, TargetType=target_type)
    rule = csn.NotificationRule(
        "TestRule",
        Name=name,
        DetailType=detail,
        EventTypeIds=event_ids,
        Resource=resource,
        Targets=[target]
    )
    
    # Get dictionary representation
    dict_repr = rule.to_dict()
    
    # Should be JSON serializable
    json_str = json.dumps(dict_repr)
    reconstructed = json.loads(json_str)
    
    # Should be the same after round-trip
    assert reconstructed == dict_repr


# Test 6: Hash consistency with None title (known bug from base class)
@given(address1=valid_arn, type1=target_type, address2=valid_arn, type2=target_type)
def test_target_hash_consistency(address1, type1, address2, type2):
    """Test hash consistency for Target objects without explicit title"""
    # Create two targets with same properties
    target1 = csn.Target(TargetAddress=address1, TargetType=type1)
    target2 = csn.Target(TargetAddress=address1, TargetType=type1)  # Same as target1
    
    # Create third target with different properties
    target3 = csn.Target(TargetAddress=address2, TargetType=type2)
    
    # Equal objects should have equal hashes
    if target1 == target2:
        assert hash(target1) == hash(target2), "Equal objects must have equal hashes"
    
    # Different objects should (usually) have different hashes
    if target1 != target3:
        # This is not strictly required but is good practice
        pass  # Hash collision is possible but unlikely


# Test 7: Set membership consistency
@given(
    addresses=st.lists(valid_arn, min_size=2, max_size=5, unique=True),
    types=st.lists(target_type, min_size=2, max_size=5)
)
def test_target_set_membership(addresses, types):
    """Test that identical Target objects behave correctly in sets"""
    assume(len(addresses) == len(types))
    
    # Create identical targets
    target1 = csn.Target(TargetAddress=addresses[0], TargetType=types[0])
    target2 = csn.Target(TargetAddress=addresses[0], TargetType=types[0])
    
    # Put one in a set
    target_set = {target1}
    
    # Identical target should be found in set
    assert target2 in target_set, "Identical object should be found in set"
    
    # Adding identical target shouldn't increase set size
    target_set.add(target2)
    assert len(target_set) == 1, "Set should not contain duplicates of identical objects"


# Test 8: Dictionary key consistency
@given(address=valid_arn, t_type=target_type, value=st.text())
def test_target_as_dict_key(address, t_type, value):
    """Test that identical Target objects work as dictionary keys"""
    target1 = csn.Target(TargetAddress=address, TargetType=t_type)
    target2 = csn.Target(TargetAddress=address, TargetType=t_type)
    
    # Use target1 as dict key
    d = {target1: value}
    
    # Should be able to access with identical target2
    try:
        retrieved = d[target2]
        assert retrieved == value
    except KeyError:
        # This indicates a bug in hash/equality
        pytest.fail("Cannot use identical object as dictionary key")


# Test 9: Optional properties handling
@given(
    name=valid_name,
    detail=detail_type,
    event_ids=st.lists(event_type_id, min_size=1, max_size=3),
    resource=valid_arn,
    target_address=valid_arn,
    target_type=target_type,
    rule_status=st.one_of(st.none(), status),
    created_by=st.one_of(st.none(), valid_string)
)
def test_notification_rule_optional_properties(name, detail, event_ids, resource, 
                                              target_address, target_type, 
                                              rule_status, created_by):
    """Test NotificationRule with optional properties"""
    target = csn.Target(TargetAddress=target_address, TargetType=target_type)
    
    kwargs = {
        'Name': name,
        'DetailType': detail,
        'EventTypeIds': event_ids,
        'Resource': resource,
        'Targets': [target]
    }
    
    if rule_status is not None:
        kwargs['Status'] = rule_status
    if created_by is not None:
        kwargs['CreatedBy'] = created_by
    
    rule = csn.NotificationRule("TestRule", **kwargs)
    result = rule.to_dict()
    
    # Check required properties are present
    assert result['Properties']['Name'] == name
    assert result['Properties']['DetailType'] == detail
    
    # Check optional properties if provided
    if rule_status is not None:
        assert result['Properties']['Status'] == rule_status
    if created_by is not None:
        assert result['Properties']['CreatedBy'] == created_by


# Test 10: Type validation for list properties
@given(
    name=valid_name,
    detail=detail_type,
    resource=valid_arn,
    target_address=valid_arn,
    target_type=target_type
)
def test_event_type_ids_must_be_list(name, detail, resource, target_address, target_type):
    """Test that EventTypeIds must be a list, not a string"""
    target = csn.Target(TargetAddress=target_address, TargetType=target_type)
    
    with pytest.raises((TypeError, AttributeError)):
        # EventTypeIds should be a list, not a string
        rule = csn.NotificationRule(
            "TestRule",
            Name=name,
            DetailType=detail,
            EventTypeIds="not-a-list",  # Wrong type
            Resource=resource,
            Targets=[target]
        )


# Test 11: Equality implementation
@given(
    name1=valid_name,
    name2=valid_name,
    detail=detail_type,
    event_ids=st.lists(event_type_id, min_size=1, max_size=2),
    resource=valid_arn,
    target_address=valid_arn,
    target_type=target_type
)
def test_notification_rule_equality(name1, name2, detail, event_ids, resource, target_address, target_type):
    """Test equality implementation for NotificationRule"""
    target = csn.Target(TargetAddress=target_address, TargetType=target_type)
    
    # Create two rules with same title and properties
    rule1 = csn.NotificationRule(
        "SameTitle",
        Name=name1,
        DetailType=detail,
        EventTypeIds=event_ids,
        Resource=resource,
        Targets=[target]
    )
    
    rule2 = csn.NotificationRule(
        "SameTitle",
        Name=name1,  # Same name as rule1
        DetailType=detail,
        EventTypeIds=event_ids,
        Resource=resource,
        Targets=[target]
    )
    
    # Create third rule with different name
    rule3 = csn.NotificationRule(
        "SameTitle",
        Name=name2,  # Different name
        DetailType=detail,
        EventTypeIds=event_ids,
        Resource=resource,
        Targets=[target]
    )
    
    # Rules with same title and properties should be equal
    assert rule1 == rule2
    
    # Rules with different properties should not be equal (unless names happen to be same)
    if name1 != name2:
        assert rule1 != rule3


if __name__ == "__main__":
    # Run all tests
    pytest.main([__file__, "-v", "--tb=short"])