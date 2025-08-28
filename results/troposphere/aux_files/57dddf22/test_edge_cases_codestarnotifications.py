#!/usr/bin/env python3
"""Edge case property-based tests for troposphere.codestarnotifications"""

import sys
import json
from hypothesis import given, assume, strategies as st, settings, example
import pytest

sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.codestarnotifications as csn
from troposphere import Ref, GetAtt, Tags


# Test for potential double validator bug
@given(threshold_value=st.one_of(
    st.floats(min_value=0, max_value=1e10, allow_nan=False, allow_infinity=False),
    st.integers(min_value=0, max_value=10000),
    st.text().map(str)  # String representations of numbers
))
def test_threshold_double_validator(threshold_value):
    """Test if NotificationRule accepts double/float values correctly"""
    # NotificationRule doesn't have a Threshold, but let's test with properties it does have
    # This is to check if there are any validator functions that might have issues
    pass


# Test property type coercion edge cases
@given(
    event_id_single=st.text(min_size=1, max_size=50),
    event_ids_list=st.lists(st.text(min_size=1, max_size=50), min_size=1, max_size=3)
)
def test_event_type_id_single_vs_list(event_id_single, event_ids_list):
    """Test EventTypeId (single) vs EventTypeIds (list) property behavior"""
    target = csn.Target(TargetAddress="arn:test", TargetType="SNS")
    
    # Test with EventTypeIds (list)
    rule1 = csn.NotificationRule(
        "Rule1",
        Name="Test",
        DetailType="BASIC",
        EventTypeIds=event_ids_list,
        Resource="arn:resource",
        Targets=[target]
    )
    
    dict1 = rule1.to_dict()
    assert 'EventTypeIds' in dict1['Properties']
    assert isinstance(dict1['Properties']['EventTypeIds'], list)
    
    # Test if EventTypeId (single) is also accepted
    if 'EventTypeId' in csn.NotificationRule.props:
        rule2 = csn.NotificationRule(
            "Rule2",
            Name="Test",
            DetailType="BASIC",
            EventTypeId=event_id_single,
            EventTypeIds=event_ids_list,
            Resource="arn:resource",
            Targets=[target]
        )
        
        dict2 = rule2.to_dict()
        # Both should be in the output
        assert 'EventTypeId' in dict2['Properties'] or 'EventTypeIds' in dict2['Properties']


# Test with CloudFormation intrinsic functions
def test_with_intrinsic_functions():
    """Test that CloudFormation intrinsic functions work correctly"""
    from troposphere import Ref, GetAtt, Parameter
    
    # Create a parameter (mock)
    topic_param = Parameter("TopicArn", Type="String")
    
    # Use Ref as TargetAddress
    try:
        target_with_ref = csn.Target(
            TargetAddress=Ref(topic_param),
            TargetType="SNS"
        )
        
        dict_repr = target_with_ref.to_dict()
        # The Ref should be preserved in the output
        assert 'Ref' in str(dict_repr)
        print("✓ Ref function works with TargetAddress")
    except Exception as e:
        print(f"✗ Cannot use Ref with TargetAddress: {e}")


# Test mutually exclusive properties
@given(
    target_address=st.text(min_size=20, max_size=100),
    targets_list=st.lists(
        st.tuples(
            st.text(min_size=20, max_size=100),
            st.sampled_from(["SNS", "AWSChatbotSlack"])
        ),
        min_size=1,
        max_size=3
    )
)
def test_target_address_vs_targets(target_address, targets_list):
    """Test TargetAddress (single) vs Targets (list) mutual exclusivity"""
    # NotificationRule has both TargetAddress and Targets in props
    # Test if they can be used together or are mutually exclusive
    
    targets = [csn.Target(TargetAddress=addr, TargetType=ttype) 
               for addr, ttype in targets_list]
    
    # Try with just Targets (should work)
    rule1 = csn.NotificationRule(
        "Rule1",
        Name="Test",
        DetailType="BASIC", 
        EventTypeIds=["event1"],
        Resource="arn:resource",
        Targets=targets
    )
    
    dict1 = rule1.to_dict()
    assert 'Targets' in dict1['Properties']
    
    # Try with both TargetAddress and Targets
    try:
        rule2 = csn.NotificationRule(
            "Rule2",
            Name="Test",
            DetailType="BASIC",
            EventTypeIds=["event1"],
            Resource="arn:resource",
            TargetAddress=target_address,  # Single address
            Targets=targets  # List of targets
        )
        
        dict2 = rule2.to_dict()
        # Check what gets included
        has_single = 'TargetAddress' in dict2['Properties']
        has_list = 'Targets' in dict2['Properties']
        
        if has_single and has_list:
            # Both are allowed - potential issue?
            pass
        elif has_list and not has_single:
            # List takes precedence
            pass
        elif has_single and not has_list:
            # Single takes precedence  
            pass
    except Exception:
        # They might be mutually exclusive
        pass


# Test empty collections
@given(empty_list=st.just([]))
def test_empty_event_type_ids(empty_list):
    """Test behavior with empty EventTypeIds list"""
    target = csn.Target(TargetAddress="arn:test", TargetType="SNS")
    
    with pytest.raises((ValueError, TypeError)):
        # Empty EventTypeIds should fail validation
        rule = csn.NotificationRule(
            "Rule",
            Name="Test",
            DetailType="BASIC",
            EventTypeIds=empty_list,  # Empty list
            Resource="arn:resource",
            Targets=[target]
        )
        rule.to_dict()


# Test property validation order
@given(
    name=st.text(min_size=1, max_size=64),
    invalid_detail=st.text(min_size=1).filter(lambda x: x not in ["BASIC", "FULL"])
)
def test_validation_order(name, invalid_detail):
    """Test order of property validation"""
    target = csn.Target(TargetAddress="arn:test", TargetType="SNS")
    
    # Create rule with invalid DetailType but missing other required properties
    with pytest.raises((ValueError, TypeError, AttributeError)):
        rule = csn.NotificationRule(
            "Rule",
            Name=name,
            DetailType=invalid_detail,  # Invalid value
            # Missing EventTypeIds, Resource, Targets
        )
        rule.to_dict()


# Test Tags property if it exists
@given(
    tag_keys=st.lists(st.text(min_size=1, max_size=127), min_size=1, max_size=5, unique=True),
    tag_values=st.lists(st.text(min_size=0, max_size=255), min_size=1, max_size=5)
)
def test_tags_property(tag_keys, tag_values):
    """Test Tags property on NotificationRule"""
    assume(len(tag_keys) == len(tag_values))
    
    target = csn.Target(TargetAddress="arn:test", TargetType="SNS")
    
    # Create tags dict
    tags_dict = dict(zip(tag_keys, tag_values))
    
    if 'Tags' in csn.NotificationRule.props:
        rule = csn.NotificationRule(
            "Rule",
            Name="Test",
            DetailType="BASIC",
            EventTypeIds=["event1"],
            Resource="arn:resource",
            Targets=[target],
            Tags=tags_dict
        )
        
        dict_repr = rule.to_dict()
        if 'Tags' in dict_repr['Properties']:
            assert dict_repr['Properties']['Tags'] == tags_dict


# Test extremely long strings
@given(
    long_string=st.text(min_size=1000, max_size=5000)
)
def test_long_string_handling(long_string):
    """Test handling of very long strings in properties"""
    target = csn.Target(TargetAddress=long_string, TargetType="SNS")
    
    # Should be able to create and serialize
    dict_repr = target.to_dict()
    assert dict_repr['TargetAddress'] == long_string
    
    # Should be JSON serializable
    json_str = json.dumps(dict_repr)
    reconstructed = json.loads(json_str)
    assert reconstructed['TargetAddress'] == long_string


# Test unicode and special characters
@given(
    unicode_string=st.text(
        alphabet=st.characters(min_codepoint=0x100, max_codepoint=0x1000),
        min_size=1,
        max_size=50
    )
)
def test_unicode_handling(unicode_string):
    """Test handling of unicode characters in properties"""
    try:
        rule = csn.NotificationRule(
            "Rule",
            Name=unicode_string,  # Unicode in name
            DetailType="BASIC",
            EventTypeIds=["event1"],
            Resource="arn:resource",
            Targets=[csn.Target(TargetAddress="arn:test", TargetType="SNS")]
        )
        
        dict_repr = rule.to_dict()
        assert dict_repr['Properties']['Name'] == unicode_string
        
        # Should be JSON serializable
        json_str = json.dumps(dict_repr)
        reconstructed = json.loads(json_str)
        assert reconstructed['Properties']['Name'] == unicode_string
    except (ValueError, TypeError):
        # Some unicode might not be valid for AWS names
        pass


if __name__ == "__main__":
    print("Running edge case tests...")
    
    # Run intrinsic functions test separately
    test_with_intrinsic_functions()
    
    # Run property-based tests
    pytest.main([__file__, "-v", "--tb=short", "-k", "not intrinsic"])