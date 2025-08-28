import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import re
from hypothesis import given, strategies as st, assume, settings
from troposphere.devopsguru import (
    NotificationChannel,
    NotificationChannelConfig,
    SnsChannelConfig,
    NotificationFilterConfig,
    ResourceCollection,
    ResourceCollectionFilter,
    CloudFormationCollectionFilter,
    TagCollection,
    LogAnomalyDetectionIntegration
)
from troposphere import BaseAWSObject


# Strategy for valid alphanumeric titles
valid_titles = st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')), min_size=1)

# Strategy for invalid titles (non-alphanumeric)
invalid_titles = st.text(min_size=1).filter(lambda x: not re.match(r'^[a-zA-Z0-9]+$', x))

# Strategy for ARNs
arns = st.text(min_size=1, max_size=200).map(lambda x: f"arn:aws:sns:us-east-1:123456789012:{x}")


@given(title=valid_titles)
def test_valid_title_accepted(title):
    """Test that valid alphanumeric titles are accepted"""
    config = NotificationChannelConfig(Sns=SnsChannelConfig(TopicArn="arn:aws:sns:us-east-1:123456789012:test"))
    nc = NotificationChannel(title, Config=config)
    assert nc.title == title
    nc.to_dict()  # Should not raise


@given(title=invalid_titles)
def test_invalid_title_rejected(title):
    """Test that non-alphanumeric titles are rejected"""
    config = NotificationChannelConfig(Sns=SnsChannelConfig(TopicArn="arn:aws:sns:us-east-1:123456789012:test"))
    try:
        nc = NotificationChannel(title, Config=config)
        nc.to_dict()  # Validation happens here
        assert False, f"Should have rejected title: {repr(title)}"
    except ValueError as e:
        assert 'not alphanumeric' in str(e)


@given(title=valid_titles)
def test_required_property_validation(title):
    """Test that required properties are enforced"""
    # NotificationChannel requires Config property
    nc = NotificationChannel(title)
    try:
        nc.to_dict()  # Should fail - Config is required
        assert False, "Should have failed due to missing required Config"
    except ValueError as e:
        assert 'required' in str(e).lower()
        assert 'Config' in str(e)


@given(
    title=valid_titles,
    topic_arn=arns,
    message_types=st.lists(st.text(min_size=1, max_size=50), max_size=5),
    severities=st.lists(st.text(min_size=1, max_size=50), max_size=5)
)
def test_serialization_round_trip(title, topic_arn, message_types, severities):
    """Test that to_dict and _from_dict are inverses"""
    # Create a complex nested structure
    filter_config = NotificationFilterConfig(
        MessageTypes=message_types,
        Severities=severities
    )
    sns_config = SnsChannelConfig(TopicArn=topic_arn)
    config = NotificationChannelConfig(Sns=sns_config, Filters=filter_config)
    original = NotificationChannel(title, Config=config)
    
    # Serialize and deserialize
    dict_repr = original.to_dict()
    reconstructed = NotificationChannel._from_dict(title, **dict_repr['Properties'])
    
    # Check they produce the same dict
    assert reconstructed.to_dict() == dict_repr


@given(
    title=valid_titles,
    wrong_type_value=st.one_of(
        st.integers(),
        st.floats(),
        st.booleans(),
        st.dictionaries(st.text(), st.text())
    )
)
def test_type_validation(title, wrong_type_value):
    """Test that type checking is enforced for properties"""
    nc = NotificationChannel(title)
    
    # Config should be a NotificationChannelConfig object, not a primitive
    try:
        nc.Config = wrong_type_value
        nc.to_dict()
        # If it accepts wrong type without error, that's a bug
        assert False, f"Should have rejected wrong type: {type(wrong_type_value)}"
    except (TypeError, AttributeError):
        pass  # Expected behavior


@given(
    title=valid_titles,
    stack_names=st.lists(st.text(min_size=1, max_size=100), min_size=0, max_size=10)
)
def test_list_property_validation(title, stack_names):
    """Test that list properties accept lists and validate types"""
    cf_filter = CloudFormationCollectionFilter(StackNames=stack_names)
    rc_filter = ResourceCollectionFilter(CloudFormation=cf_filter)
    rc = ResourceCollection(title, ResourceCollectionFilter=rc_filter)
    
    dict_repr = rc.to_dict()
    assert 'Properties' in dict_repr
    if stack_names:
        assert dict_repr['Properties']['ResourceCollectionFilter']['CloudFormation']['StackNames'] == stack_names


@given(
    title=valid_titles,
    tag_key=st.text(min_size=1, max_size=100),
    tag_values=st.lists(st.text(min_size=1, max_size=100), min_size=1, max_size=10)
)
def test_nested_validation_propagates(title, tag_key, tag_values):
    """Test that validation works for deeply nested structures"""
    tag_collection = TagCollection(AppBoundaryKey=tag_key, TagValues=tag_values)
    rc_filter = ResourceCollectionFilter(Tags=[tag_collection])
    rc = ResourceCollection(title, ResourceCollectionFilter=rc_filter)
    
    dict_repr = rc.to_dict()
    # Verify nested structure is preserved
    tags = dict_repr['Properties']['ResourceCollectionFilter']['Tags']
    assert len(tags) == 1
    assert tags[0]['AppBoundaryKey'] == tag_key
    assert tags[0]['TagValues'] == tag_values


@given(data=st.data())
def test_empty_object_validation(data):
    """Test that objects with no required properties can be instantiated empty"""
    # LogAnomalyDetectionIntegration has no required properties
    title = data.draw(valid_titles)
    obj = LogAnomalyDetectionIntegration(title)
    dict_repr = obj.to_dict()
    assert 'Type' in dict_repr
    assert dict_repr['Type'] == 'AWS::DevOpsGuru::LogAnomalyDetectionIntegration'


@given(
    title=valid_titles,
    extra_key=st.text(min_size=1, max_size=50).filter(lambda x: x not in ['Config'])
)
def test_unknown_property_rejected(title, extra_key):
    """Test that unknown properties are rejected"""
    nc = NotificationChannel(title)
    try:
        setattr(nc, extra_key, "some_value")
        # If it's truly unknown, it should raise AttributeError
        if extra_key not in nc.properties and extra_key not in nc.resource:
            assert False, f"Should have rejected unknown property: {extra_key}"
    except AttributeError as e:
        assert 'does not support attribute' in str(e)