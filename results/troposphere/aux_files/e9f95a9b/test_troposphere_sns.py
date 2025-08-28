"""Property-based tests for troposphere.sns module."""

import string
from hypothesis import given, strategies as st, assume, settings
import troposphere.sns as sns
import json


# Test 1: Boolean string conversion consistency
@given(st.text(min_size=1, max_size=10))
def test_boolean_string_conversion_consistency(text):
    """Test that boolean conversion is consistent for case variations."""
    topic = sns.Topic('TestTopic')
    
    # If lowercase version works, uppercase should too (or vice versa)
    lowercase = text.lower()
    uppercase = text.upper()
    
    lowercase_works = False
    uppercase_works = False
    
    try:
        topic.FifoTopic = lowercase
        lowercase_result = topic.properties.get('FifoTopic')
        lowercase_works = True
    except:
        pass
    
    try:
        topic.FifoTopic = uppercase
        uppercase_result = topic.properties.get('FifoTopic')
        uppercase_works = True
    except:
        pass
    
    # If one works, check if behavior is consistent
    if lowercase_works and uppercase_works:
        # Both work - they should produce same result
        assert lowercase_result == uppercase_result, f"Case inconsistency: {lowercase!r}->{lowercase_result} vs {uppercase!r}->{uppercase_result}"


# Test 2: Boolean numeric string conversion
@given(st.integers())
def test_boolean_numeric_string_conversion(num):
    """Test that numeric strings are handled consistently with their numeric values."""
    topic = sns.Topic('TestTopic')
    
    # Test numeric value
    try:
        topic.FifoTopic = num
        numeric_result = topic.properties.get('FifoTopic')
        numeric_works = True
    except:
        numeric_works = False
    
    # Test string version
    try:
        topic.FifoTopic = str(num)
        string_result = topic.properties.get('FifoTopic')
        string_works = True
    except:
        string_works = False
    
    # If numeric works, string should work the same way for 0 and 1
    if num in [0, 1] and numeric_works:
        assert string_works, f"String '{num}' should work if numeric {num} works"
        assert numeric_result == string_result, f"Inconsistent conversion: {num}->{numeric_result} vs '{num}'->{string_result}"


# Test 3: Subscription list property handling
@given(st.lists(
    st.builds(
        sns.Subscription,
        Protocol=st.sampled_from(['http', 'https', 'email', 'sms', 'lambda', 'sqs']),
        Endpoint=st.text(min_size=1, max_size=100)
    ),
    max_size=10
))
def test_subscription_list_preservation(subscriptions):
    """Test that subscription lists are preserved correctly in to_dict."""
    topic = sns.Topic('TestTopic')
    topic.Subscription = subscriptions
    
    # Convert to dict
    result = topic.to_dict()
    
    # Check subscriptions are preserved
    if subscriptions:
        assert 'Subscription' in result['Properties']
        result_subs = result['Properties']['Subscription']
        assert len(result_subs) == len(subscriptions)
        
        for i, (orig, res) in enumerate(zip(subscriptions, result_subs)):
            assert res['Protocol'] == orig.Protocol, f"Protocol mismatch at index {i}"
            assert res['Endpoint'] == orig.Endpoint, f"Endpoint mismatch at index {i}"
    else:
        # Empty list should still be in properties
        assert result['Properties'].get('Subscription', []) == []


# Test 4: Property type validation for strings
@given(st.one_of(
    st.text(min_size=0, max_size=1000),
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.lists(st.text(), max_size=5),
    st.dictionaries(st.text(min_size=1, max_size=10), st.text(), max_size=5)
))
def test_string_property_type_handling(value):
    """Test that string properties handle type validation correctly."""
    topic = sns.Topic('TestTopic')
    
    # DisplayName should be a string
    try:
        topic.DisplayName = value
        result = topic.properties.get('DisplayName')
        
        # Should only work for strings
        if not isinstance(value, str):
            # If it worked, it should have been converted to string
            assert isinstance(result, str), f"Non-string {type(value).__name__} not converted: {result!r}"
    except Exception as e:
        # Should fail for non-strings
        assert not isinstance(value, str), f"String {value!r} should not have failed"


# Test 5: JSON serialization round-trip
@given(
    display_name=st.text(min_size=0, max_size=100),
    topic_name=st.text(min_size=1, max_size=50),
    kms_key=st.text(min_size=0, max_size=100),
    fifo=st.booleans(),
    dedup=st.booleans()
)
def test_json_serialization_round_trip(display_name, topic_name, kms_key, fifo, dedup):
    """Test that properties survive JSON serialization."""
    topic = sns.Topic('TestTopic')
    
    if display_name:
        topic.DisplayName = display_name
    topic.TopicName = topic_name
    if kms_key:
        topic.KmsMasterKeyId = kms_key
    topic.FifoTopic = fifo
    topic.ContentBasedDeduplication = dedup
    
    # Convert to dict, then to JSON, then back
    dict1 = topic.to_dict()
    json_str = json.dumps(dict1)
    dict2 = json.loads(json_str)
    
    # Properties should be preserved
    props1 = dict1['Properties']
    props2 = dict2['Properties']
    
    for key in props1:
        assert props2[key] == props1[key], f"Property {key} not preserved: {props1[key]!r} != {props2[key]!r}"


# Test 6: FIFO topic name constraint
@given(st.text(min_size=1, max_size=50))
def test_fifo_topic_name_validation(name):
    """Test FIFO topic naming constraints."""
    topic = sns.Topic('TestTopic')
    topic.FifoTopic = True
    topic.TopicName = name
    
    # AWS requires FIFO topics to end with .fifo
    # But does troposphere enforce this?
    result = topic.to_dict()
    
    # Check if validation happens
    if result['Properties'].get('FifoTopic'):
        topic_name = result['Properties'].get('TopicName', '')
        # This is what SHOULD happen according to AWS docs
        # Let's see if troposphere enforces it
        pass  # No assertion - just testing current behavior


# Test 7: Empty subscription endpoint
@given(st.sampled_from(['http', 'https', 'email', 'sms', 'lambda']))
def test_empty_endpoint_subscription(protocol):
    """Test subscription with empty endpoint."""
    # Endpoint is marked as required in props
    try:
        sub = sns.Subscription(Protocol=protocol, Endpoint='')
        topic = sns.Topic('Test')
        topic.Subscription = [sub]
        result = topic.to_dict()
        
        # Empty string endpoint should be preserved
        assert result['Properties']['Subscription'][0]['Endpoint'] == ''
    except Exception as e:
        # Should not fail for empty string (it's still a string)
        assert False, f"Empty endpoint should be allowed: {e}"


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])