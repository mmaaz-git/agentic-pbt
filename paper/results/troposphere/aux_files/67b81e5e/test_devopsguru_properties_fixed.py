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


# Strategy for valid ASCII alphanumeric titles (what the code actually accepts)
ascii_alphanumeric_titles = st.text(alphabet=st.characters(whitelist_categories=(), whitelist_characters='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'), min_size=1)

# Strategy for Unicode alphanumeric that Python considers alphanumeric but troposphere rejects
unicode_alphanumeric_titles = st.text(min_size=1).filter(
    lambda x: x.isalnum() and not re.match(r'^[a-zA-Z0-9]+$', x)
)

# Strategy for ARNs
arns = st.text(min_size=1, max_size=200).map(lambda x: f"arn:aws:sns:us-east-1:123456789012:{x}")


@given(title=unicode_alphanumeric_titles)
@settings(max_examples=100)
def test_misleading_alphanumeric_error_message(title):
    """Test that Unicode alphanumeric characters trigger misleading error message"""
    config = NotificationChannelConfig(Sns=SnsChannelConfig(TopicArn="arn:aws:sns:us-east-1:123456789012:test"))
    try:
        nc = NotificationChannel(title, Config=config)
        nc.to_dict()
        assert False, f"Should have rejected title: {repr(title)}"
    except ValueError as e:
        # The error says "not alphanumeric" but the title IS alphanumeric by Python standards
        assert 'not alphanumeric' in str(e)
        assert title.isalnum(), f"Title {repr(title)} is alphanumeric by Python's isalnum()"


@given(title=ascii_alphanumeric_titles)
def test_required_property_validation_fixed(title):
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
    title=ascii_alphanumeric_titles,
    topic_arn=arns,
    message_types=st.lists(st.text(min_size=1, max_size=50), max_size=5),
    severities=st.lists(st.text(min_size=1, max_size=50), max_size=5)
)
def test_serialization_round_trip_fixed(title, topic_arn, message_types, severities):
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
    title=ascii_alphanumeric_titles,
    invalid_config=st.one_of(
        st.text(),
        st.integers(),
        st.floats(),
        st.booleans(),
        st.lists(st.text())
    )
)
def test_type_validation_for_config(title, invalid_config):
    """Test that Config property must be correct type"""
    nc = NotificationChannel(title)
    
    # Config should be a NotificationChannelConfig object
    try:
        nc.Config = invalid_config
        # Try to trigger validation
        dict_repr = nc.to_dict()
        # Check if wrong type was silently accepted
        if not isinstance(dict_repr.get('Properties', {}).get('Config'), dict):
            assert False, f"Accepted invalid Config type: {type(invalid_config)}"
    except (TypeError, AttributeError, ValueError):
        pass  # Expected - wrong type rejected


@given(
    title=ascii_alphanumeric_titles,
    invalid_list=st.one_of(
        st.text(),
        st.integers(), 
        st.dictionaries(st.text(), st.text())
    )
)
def test_list_property_type_checking(title, invalid_list):
    """Test that list properties reject non-list values"""
    cf_filter = CloudFormationCollectionFilter()
    
    # StackNames should be a list
    try:
        cf_filter.StackNames = invalid_list
        # Force validation
        rc_filter = ResourceCollectionFilter(CloudFormation=cf_filter)
        rc = ResourceCollection(title, ResourceCollectionFilter=rc_filter)
        rc.to_dict()
        
        # If we got here without error, check what was stored
        dict_repr = rc.to_dict()
        stack_names = dict_repr.get('Properties', {}).get('ResourceCollectionFilter', {}).get('CloudFormation', {}).get('StackNames')
        if stack_names is not None and not isinstance(stack_names, list):
            assert False, f"Non-list value accepted for StackNames: {type(invalid_list)}"
    except (TypeError, AttributeError):
        pass  # Expected behavior


@given(title=ascii_alphanumeric_titles)
def test_validation_with_no_validation_flag(title):
    """Test that validation can be disabled"""
    # Create object without required property
    nc = NotificationChannel(title)
    nc.no_validation()
    
    # Should succeed even without required Config
    dict_repr = nc.to_dict(validation=False)
    assert 'Type' in dict_repr
    
    # But with validation it should fail
    nc2 = NotificationChannel(title)
    try:
        nc2.to_dict(validation=True)
        assert False, "Should have failed validation"
    except ValueError:
        pass


@given(
    title=ascii_alphanumeric_titles,
    tags_list=st.lists(
        st.fixed_dictionaries({
            'AppBoundaryKey': st.text(min_size=1, max_size=50),
            'TagValues': st.lists(st.text(min_size=1, max_size=50), min_size=1, max_size=5)
        }),
        min_size=1,
        max_size=3
    )
)
def test_complex_nested_structures(title, tags_list):
    """Test complex nested list of objects"""
    tag_collections = []
    for tag_dict in tags_list:
        tc = TagCollection(
            AppBoundaryKey=tag_dict['AppBoundaryKey'],
            TagValues=tag_dict['TagValues']
        )
        tag_collections.append(tc)
    
    rc_filter = ResourceCollectionFilter(Tags=tag_collections)
    rc = ResourceCollection(title, ResourceCollectionFilter=rc_filter)
    
    dict_repr = rc.to_dict()
    
    # Verify the structure is preserved
    result_tags = dict_repr['Properties']['ResourceCollectionFilter']['Tags']
    assert len(result_tags) == len(tags_list)
    for i, tag in enumerate(result_tags):
        assert tag['AppBoundaryKey'] == tags_list[i]['AppBoundaryKey']
        assert tag['TagValues'] == tags_list[i]['TagValues']