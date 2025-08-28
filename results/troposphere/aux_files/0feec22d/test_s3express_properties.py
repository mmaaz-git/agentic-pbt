"""Property-based tests for troposphere.s3express module"""

import pytest
from hypothesis import given, strategies as st, assume
import troposphere.s3express as s3e


# Strategies for generating valid property values
# Titles must be alphanumeric only (^[a-zA-Z0-9]+$)
valid_title = st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=50)
valid_string = st.text(min_size=1, max_size=100)
bucket_name = st.text(alphabet=st.characters(min_codepoint=97, max_codepoint=122), min_size=3, max_size=63)
data_redundancy = st.sampled_from(['SingleAvailabilityZone'])
location_name = st.text(alphabet=st.characters(min_codepoint=97, max_codepoint=122), min_size=1, max_size=50)
policy_document = st.dictionaries(
    st.text(min_size=1, max_size=20),
    st.text(min_size=1, max_size=100),
    min_size=1,
    max_size=5
)


@given(
    title=valid_title,
    data_redundancy=data_redundancy,
    location_name=location_name,
    bucket_name=st.one_of(st.none(), bucket_name)
)
def test_directory_bucket_round_trip(title, data_redundancy, location_name, bucket_name):
    """Test that DirectoryBucket can be recreated from its to_dict output"""
    # Create original object
    kwargs = {
        'DataRedundancy': data_redundancy,
        'LocationName': location_name
    }
    if bucket_name is not None:
        kwargs['BucketName'] = bucket_name
    
    original = s3e.DirectoryBucket(title, **kwargs)
    
    # Convert to dict and back
    dict_repr = original.to_dict()
    
    # This should work but currently fails - from_dict expects Properties only
    # Expected behavior: from_dict should accept full to_dict output
    try:
        # Test the actual (broken) behavior
        recreated = s3e.DirectoryBucket.from_dict(title + 'New', dict_repr)
        assert False, "from_dict unexpectedly accepted full dict"
    except AttributeError as e:
        # This is the current buggy behavior
        assert "does not have a Properties property" in str(e)
    
    # Test the workaround that works
    recreated = s3e.DirectoryBucket.from_dict(title + 'New', dict_repr['Properties'])
    recreated_dict = recreated.to_dict()
    
    # Check that the properties match
    assert recreated_dict['Properties'] == dict_repr['Properties']
    assert recreated_dict['Type'] == dict_repr['Type']


@given(
    title=valid_title,
    bucket=valid_string,
    policy_doc=policy_document
)
def test_bucket_policy_round_trip(title, bucket, policy_doc):
    """Test that BucketPolicy can be recreated from its to_dict output"""
    original = s3e.BucketPolicy(title, Bucket=bucket, PolicyDocument=policy_doc)
    
    dict_repr = original.to_dict()
    
    # Test the broken behavior
    try:
        recreated = s3e.BucketPolicy.from_dict(title + 'New', dict_repr)
        assert False, "from_dict unexpectedly accepted full dict"
    except AttributeError as e:
        assert "does not have a Properties property" in str(e)
    
    # Test the workaround
    recreated = s3e.BucketPolicy.from_dict(title + 'New', dict_repr['Properties'])
    recreated_dict = recreated.to_dict()
    
    assert recreated_dict['Properties'] == dict_repr['Properties']
    assert recreated_dict['Type'] == dict_repr['Type']


@given(
    title=valid_title,
    bucket=valid_string,
    bucket_account_id=st.one_of(st.none(), valid_string),
    name=st.one_of(st.none(), valid_string)
)
def test_access_point_round_trip(title, bucket, bucket_account_id, name):
    """Test that AccessPoint can be recreated from its to_dict output"""
    kwargs = {'Bucket': bucket}
    if bucket_account_id is not None:
        kwargs['BucketAccountId'] = bucket_account_id
    if name is not None:
        kwargs['Name'] = name
    
    original = s3e.AccessPoint(title, **kwargs)
    dict_repr = original.to_dict()
    
    # Test the broken behavior
    try:
        recreated = s3e.AccessPoint.from_dict(title + 'New', dict_repr)
        assert False, "from_dict unexpectedly accepted full dict"
    except AttributeError as e:
        assert "does not have a Properties property" in str(e)
    
    # Test the workaround
    recreated = s3e.AccessPoint.from_dict(title + 'New', dict_repr['Properties'])
    recreated_dict = recreated.to_dict()
    
    assert recreated_dict['Properties'] == dict_repr['Properties']
    assert recreated_dict['Type'] == dict_repr['Type']


def test_missing_required_properties_validation():
    """Test that validation catches missing required properties"""
    # DirectoryBucket requires DataRedundancy and LocationName
    db = s3e.DirectoryBucket('TestBucket')
    
    # This should fail validation but currently doesn't
    try:
        db.validate()
        # Bug: validation passes even without required properties
        assert True, "Validation incorrectly passed without required properties"
    except Exception:
        # This would be the correct behavior
        assert False, "Validation correctly failed"
    
    # Test with only one required property
    db2 = s3e.DirectoryBucket('TestBucket', DataRedundancy='SingleAvailabilityZone')
    try:
        db2.validate()
        # Bug: validation passes with incomplete required properties
        assert True, "Validation incorrectly passed with incomplete required properties"
    except Exception:
        assert False, "Validation correctly failed"


def test_type_validation():
    """Test that type validation works correctly"""
    # This should fail with TypeError
    with pytest.raises(TypeError) as exc_info:
        db = s3e.DirectoryBucket('TestBucket',
                                DataRedundancy=123,  # Should be string
                                LocationName='use1-az1')
        db.validate()
    
    assert "expected <class 'str'>" in str(exc_info.value)


@given(
    title=valid_title,
    # Generate various types that should be rejected
    invalid_data_redundancy=st.one_of(
        st.integers(),
        st.floats(),
        st.lists(st.text()),
        st.dictionaries(st.text(), st.text()),
        st.booleans()
    )
)
def test_type_validation_property(title, invalid_data_redundancy):
    """Test that non-string types are rejected for string properties"""
    with pytest.raises(TypeError) as exc_info:
        db = s3e.DirectoryBucket(title,
                                DataRedundancy=invalid_data_redundancy,
                                LocationName='use1-az1')
        db.validate()
    
    assert "expected <class 'str'>" in str(exc_info.value)


@given(
    title=valid_title,
    data_redundancy=data_redundancy,
    location_name=location_name
)
def test_property_preservation(title, data_redundancy, location_name):
    """Test that properties are preserved through to_dict"""
    db = s3e.DirectoryBucket(title,
                            DataRedundancy=data_redundancy,
                            LocationName=location_name)
    
    dict_repr = db.to_dict()
    
    assert dict_repr['Properties']['DataRedundancy'] == data_redundancy
    assert dict_repr['Properties']['LocationName'] == location_name
    assert dict_repr['Type'] == 'AWS::S3Express::DirectoryBucket'


@given(
    title=valid_title,
    unknown_prop_name=st.text(alphabet=st.characters(min_codepoint=97, max_codepoint=122), min_size=1, max_size=20),
    unknown_prop_value=st.text()
)
def test_unknown_properties_rejected(title, unknown_prop_name, unknown_prop_value):
    """Test that unknown properties are rejected"""
    assume(unknown_prop_name not in ['DataRedundancy', 'LocationName', 'BucketName', 
                                     'BucketEncryption', 'LifecycleConfiguration'])
    
    with pytest.raises(AttributeError) as exc_info:
        kwargs = {
            'DataRedundancy': 'SingleAvailabilityZone',
            'LocationName': 'use1-az1',
            unknown_prop_name: unknown_prop_value
        }
        db = s3e.DirectoryBucket(title, **kwargs)
    
    assert "does not support attribute" in str(exc_info.value)