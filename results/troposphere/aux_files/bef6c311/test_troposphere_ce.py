#!/usr/bin/env python3
"""Property-based tests for troposphere.ce module"""

import sys
import json
import math
from hypothesis import given, assume, strategies as st, settings
import pytest

# Add troposphere to path
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.ce as ce
from troposphere.validators import double


# Strategy for valid string keys/values
valid_string = st.text(min_size=1, max_size=255).filter(lambda x: x.strip())

# Strategy for valid doubles - testing the double validator
# The double validator accepts anything that can be converted to float
doubles = st.one_of(
    st.floats(allow_nan=False, allow_infinity=False),
    st.integers(),
    st.text().filter(lambda x: x.strip() and x.replace('.','').replace('-','').replace('+','').replace('e','').replace('E','').isdigit()),
)

# Test 1: ResourceTag property validation and serialization
@given(key=valid_string, value=valid_string)
def test_resource_tag_roundtrip(key, value):
    """Test that ResourceTag can be created and serialized correctly"""
    tag = ce.ResourceTag(Key=key, Value=value)
    
    # Check to_dict produces expected structure
    result = tag.to_dict()
    assert result['Key'] == key
    assert result['Value'] == value
    
    # Check properties are accessible
    assert tag.Key == key
    assert tag.Value == value


# Test 2: ResourceTag requires both Key and Value
@given(key=valid_string)
def test_resource_tag_missing_value_fails(key):
    """Test that ResourceTag fails without required Value property"""
    with pytest.raises((ValueError, TypeError)):
        tag = ce.ResourceTag(Key=key)
        tag.to_dict()  # Validation happens here


@given(value=valid_string)
def test_resource_tag_missing_key_fails(value):
    """Test that ResourceTag fails without required Key property"""
    with pytest.raises((ValueError, TypeError)):
        tag = ce.ResourceTag(Value=value)
        tag.to_dict()  # Validation happens here


# Test 3: Double validator property
@given(threshold=st.floats(min_value=0.0, max_value=1e10, allow_nan=False, allow_infinity=False))
def test_anomaly_subscription_threshold_accepts_floats(threshold):
    """Test that AnomalySubscription Threshold property accepts valid floats"""
    # Create minimal valid subscription
    subscriber = ce.Subscriber(Address="test@example.com", Type="EMAIL")
    
    subscription = ce.AnomalySubscription(
        SubscriptionName="TestSub",
        Frequency="DAILY",
        MonitorArnList=["arn:aws:ce:us-east-1:123456789012:anomalymonitor/test"],
        Subscribers=[subscriber],
        Threshold=threshold
    )
    
    result = subscription.to_dict()
    # The threshold should be in the result
    assert 'Properties' in result
    assert 'Threshold' in result['Properties']
    # It should be the same value (or very close for floats)
    assert math.isclose(float(result['Properties']['Threshold']), threshold, rel_tol=1e-9)


# Test 4: Double validator validation
@given(invalid_threshold=st.one_of(
    st.text(min_size=1).filter(lambda x: not x.strip().replace('.','').replace('-','').replace('+','').replace('e','').replace('E','').isdigit()),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.text()),
))
def test_double_validator_rejects_invalid_input(invalid_threshold):
    """Test that double validator rejects non-numeric input"""
    with pytest.raises((ValueError, TypeError)):
        double(invalid_threshold)


# Test 5: Subscriber property validation
@given(
    address=valid_string,
    sub_type=st.sampled_from(["EMAIL", "SNS"]),  # Common valid types
    status=st.one_of(st.none(), st.sampled_from(["ACTIVE", "INACTIVE"]))
)
def test_subscriber_creation(address, sub_type, status):
    """Test Subscriber creation with valid properties"""
    if status is not None:
        subscriber = ce.Subscriber(Address=address, Type=sub_type, Status=status)
        result = subscriber.to_dict()
        assert result['Status'] == status
    else:
        subscriber = ce.Subscriber(Address=address, Type=sub_type)
        result = subscriber.to_dict()
    
    assert result['Address'] == address
    assert result['Type'] == sub_type


# Test 6: AnomalyMonitor required properties
@given(
    name=valid_string,
    monitor_type=st.sampled_from(["DIMENSIONAL", "CUSTOM"]),
    dimension=st.one_of(st.none(), st.sampled_from(["SERVICE", "LINKED_ACCOUNT"]))
)  
def test_anomaly_monitor_creation(name, monitor_type, dimension):
    """Test AnomalyMonitor creation with required and optional properties"""
    if dimension:
        monitor = ce.AnomalyMonitor(
            MonitorName=name,
            MonitorType=monitor_type,
            MonitorDimension=dimension
        )
        result = monitor.to_dict()
        assert result['Properties']['MonitorDimension'] == dimension
    else:
        monitor = ce.AnomalyMonitor(
            MonitorName=name,
            MonitorType=monitor_type
        )
        result = monitor.to_dict()
    
    assert result['Type'] == 'AWS::CE::AnomalyMonitor'
    assert result['Properties']['MonitorName'] == name
    assert result['Properties']['MonitorType'] == monitor_type


# Test 7: CostCategory validation
@given(
    name=valid_string,
    rule_version=st.text(min_size=1, max_size=10),
    rules=st.text(min_size=1)  # JSON string for rules
)
def test_cost_category_creation(name, rule_version, rules):
    """Test CostCategory creation with required properties"""
    category = ce.CostCategory(
        Name=name,
        RuleVersion=rule_version,
        Rules=rules
    )
    
    result = category.to_dict()
    assert result['Type'] == 'AWS::CE::CostCategory'
    assert result['Properties']['Name'] == name
    assert result['Properties']['RuleVersion'] == rule_version
    assert result['Properties']['Rules'] == rules


# Test 8: Property-based test for to_dict() method integrity
@given(
    keys=st.lists(valid_string, min_size=1, max_size=5, unique=True),
    values=st.lists(valid_string, min_size=1, max_size=5)
)
def test_resource_tags_list_serialization(keys, values):
    """Test that lists of ResourceTags serialize correctly"""
    # Make sure we have the same number of keys and values
    assume(len(keys) == len(values))
    
    tags = [ce.ResourceTag(Key=k, Value=v) for k, v in zip(keys, values)]
    
    # Create an object that uses ResourceTags
    monitor = ce.AnomalyMonitor(
        MonitorName="TestMonitor",
        MonitorType="DIMENSIONAL",
        ResourceTags=tags
    )
    
    result = monitor.to_dict()
    
    # Check that tags are properly serialized
    assert 'Properties' in result
    assert 'ResourceTags' in result['Properties']
    
    result_tags = result['Properties']['ResourceTags']
    assert len(result_tags) == len(tags)
    
    for i, tag_dict in enumerate(result_tags):
        assert tag_dict['Key'] == keys[i]
        assert tag_dict['Value'] == values[i]


# Test 9: Edge case - empty strings (if allowed)
def test_empty_string_validation():
    """Test how the module handles empty strings"""
    # Most AWS resources don't allow empty strings for required fields
    with pytest.raises((ValueError, TypeError)):
        tag = ce.ResourceTag(Key="", Value="test")
        # Force validation
        tag.to_dict()


# Test 10: Test JSON serialization invariant
@given(
    key=valid_string,
    value=valid_string,
    name=valid_string,
    monitor_type=st.sampled_from(["DIMENSIONAL", "CUSTOM"])
)
def test_json_serialization_invariant(key, value, name, monitor_type):
    """Test that to_dict() output can be serialized to JSON and back"""
    tag = ce.ResourceTag(Key=key, Value=value)
    monitor = ce.AnomalyMonitor(
        MonitorName=name,
        MonitorType=monitor_type,
        ResourceTags=[tag]
    )
    
    # Get dictionary representation
    dict_repr = monitor.to_dict()
    
    # Should be JSON serializable
    json_str = json.dumps(dict_repr)
    reconstructed = json.loads(json_str)
    
    # Should be the same after round-trip
    assert reconstructed == dict_repr


if __name__ == "__main__":
    # Run all tests
    pytest.main([__file__, "-v"])