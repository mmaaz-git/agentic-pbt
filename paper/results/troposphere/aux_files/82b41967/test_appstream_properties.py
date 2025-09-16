#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import pytest
from troposphere import appstream
from troposphere.validators import integer

# Strategy for valid S3 bucket and key names
valid_s3_names = st.text(min_size=1, max_size=255).filter(lambda x: x.strip() != "")

# Strategy for integers (testing both int and string representations)
integer_strategy = st.one_of(
    st.integers(min_value=0, max_value=10000),
    st.integers(min_value=0, max_value=10000).map(str)
)

# Property 1: Required field validation - to_dict() should fail for missing required fields
@given(
    bucket=st.one_of(st.none(), valid_s3_names),
    key=st.one_of(st.none(), valid_s3_names)
)
def test_required_field_validation(bucket, key):
    """Test that to_dict() validates required fields correctly"""
    # Create S3Location with potentially missing fields
    kwargs = {}
    if bucket is not None:
        kwargs['S3Bucket'] = bucket
    if key is not None:
        kwargs['S3Key'] = key
    
    s3 = appstream.S3Location(**kwargs)
    
    # Should succeed only if both required fields are present
    if bucket is not None and key is not None:
        result = s3.to_dict()
        assert 'S3Bucket' in result
        assert 'S3Key' in result
        assert result['S3Bucket'] == bucket
        assert result['S3Key'] == key
    else:
        with pytest.raises(ValueError):
            s3.to_dict()


# Property 2: Validation bypass - objects with validation=False should serialize even with missing fields
@given(
    name=st.one_of(st.none(), valid_s3_names),
    source_bucket=st.one_of(st.none(), valid_s3_names),
    source_key=st.one_of(st.none(), valid_s3_names)
)
def test_validation_bypass(name, source_bucket, source_key):
    """Test that validation=False allows serialization of incomplete objects"""
    kwargs = {'validation': False}
    
    if name is not None:
        kwargs['Name'] = name
    
    if source_bucket is not None and source_key is not None:
        kwargs['SourceS3Location'] = appstream.S3Location(
            S3Bucket=source_bucket,
            S3Key=source_key
        )
    
    # Should always succeed with validation=False
    ab = appstream.AppBlock("TestBlock", **kwargs)
    result = ab.to_dict()
    
    # Should always have Type field
    assert 'Type' in result
    assert result['Type'] == 'AWS::AppStream::AppBlock'
    
    # Properties should be present if we provided them
    if 'Name' in kwargs or 'SourceS3Location' in kwargs:
        assert 'Properties' in result
        if name is not None:
            assert result['Properties']['Name'] == name


# Property 3: Round-trip consistency - valid objects should serialize correctly
@given(
    bucket=valid_s3_names,
    key=valid_s3_names
)
def test_round_trip_consistency(bucket, key):
    """Test that to_dict() accurately represents the object"""
    s3 = appstream.S3Location(S3Bucket=bucket, S3Key=key)
    result = s3.to_dict()
    
    # Should contain exactly what we put in
    assert result == {'S3Bucket': bucket, 'S3Key': key}
    
    # No extra fields should appear
    assert len(result) == 2


# Property 4: Type preservation in ComputeCapacity
@given(
    desired_instances=st.one_of(
        st.none(),
        st.integers(min_value=0, max_value=10000),
        st.integers(min_value=0, max_value=10000).map(str)
    ),
    desired_sessions=st.one_of(
        st.none(),
        st.integers(min_value=0, max_value=10000),
        st.integers(min_value=0, max_value=10000).map(str)
    )
)
def test_compute_capacity_type_preservation(desired_instances, desired_sessions):
    """Test that ComputeCapacity preserves the types of values passed to it"""
    kwargs = {}
    expected = {}
    
    if desired_instances is not None:
        kwargs['DesiredInstances'] = desired_instances
        expected['DesiredInstances'] = desired_instances
    
    if desired_sessions is not None:
        kwargs['DesiredSessions'] = desired_sessions
        expected['DesiredSessions'] = desired_sessions
    
    compute = appstream.ComputeCapacity(**kwargs)
    result = compute.to_dict()
    
    # Values should be preserved as-is
    assert result == expected


# Property 5: Nested object handling
@given(
    bucket=valid_s3_names,
    key=valid_s3_names,
    timeout=st.integers(min_value=1, max_value=3600),
    executable_path=valid_s3_names
)
def test_nested_object_serialization(bucket, key, timeout, executable_path):
    """Test that nested AWSProperty objects are properly converted"""
    s3_location = appstream.S3Location(S3Bucket=bucket, S3Key=key)
    
    script = appstream.ScriptDetails(
        ScriptS3Location=s3_location,
        TimeoutInSeconds=timeout,
        ExecutablePath=executable_path
    )
    
    result = script.to_dict()
    
    # Check structure
    assert 'ScriptS3Location' in result
    assert 'TimeoutInSeconds' in result
    assert 'ExecutablePath' in result
    
    # Nested object should be converted to dict
    assert isinstance(result['ScriptS3Location'], dict)
    assert result['ScriptS3Location'] == {'S3Bucket': bucket, 'S3Key': key}
    assert result['TimeoutInSeconds'] == timeout
    assert result['ExecutablePath'] == executable_path


# Property 6: Integer validator function
@given(
    value=st.one_of(
        st.integers(),
        st.text(),
        st.floats(),
        st.booleans(),
        st.none()
    )
)
def test_integer_validator(value):
    """Test the integer validator function behavior"""
    try:
        result = integer(value)
        # If it succeeds, it should return an integer or string representation
        if isinstance(value, (int, str)):
            try:
                int(str(value))  # Should be convertible to int
                assert result == value
            except (ValueError, TypeError):
                # Should have raised an exception
                pytest.fail(f"integer() should have raised exception for {value}")
        else:
            # Non-integer types should raise exception
            pytest.fail(f"integer() should have raised exception for type {type(value)}")
    except (ValueError, TypeError):
        # Should only fail for non-integer-like values
        if isinstance(value, int):
            pytest.fail(f"integer() should not raise exception for int {value}")
        elif isinstance(value, str):
            try:
                int(value)
                pytest.fail(f"integer() should not raise exception for numeric string {value}")
            except (ValueError, TypeError):
                pass  # Expected to fail for non-numeric strings


# Property 7: Tags validation
@given(
    tags=st.one_of(
        st.none(),
        st.lists(
            st.dictionaries(
                st.just('Key'),
                valid_s3_names,
                min_size=1,
                max_size=1
            ).map(lambda d: {**d, 'Value': 'test_value'}),
            max_size=5
        ),
        st.dictionaries(valid_s3_names, valid_s3_names, max_size=5)
    )
)
def test_tags_handling(tags):
    """Test that tags are handled correctly in AppBlock"""
    kwargs = {
        'Name': 'TestBlock',
        'SourceS3Location': appstream.S3Location(S3Bucket='bucket', S3Key='key')
    }
    
    if tags is not None:
        kwargs['Tags'] = tags
    
    ab = appstream.AppBlock('TestAppBlock', **kwargs)
    result = ab.to_dict()
    
    assert 'Type' in result
    assert 'Properties' in result
    
    if tags is not None:
        assert 'Tags' in result['Properties']


# Property 8: AccessEndpoint validation
@given(
    endpoint_type=valid_s3_names,
    vpce_id=valid_s3_names
)
def test_access_endpoint_required_fields(endpoint_type, vpce_id):
    """Test AccessEndpoint with required fields"""
    endpoint = appstream.AccessEndpoint(
        EndpointType=endpoint_type,
        VpceId=vpce_id
    )
    
    result = endpoint.to_dict()
    assert result == {
        'EndpointType': endpoint_type,
        'VpceId': vpce_id
    }


# Property 9: List properties handling
@given(
    security_groups=st.lists(valid_s3_names, max_size=5),
    subnets=st.lists(valid_s3_names, max_size=5)
)
def test_vpc_config_list_properties(security_groups, subnets):
    """Test that VpcConfig handles list properties correctly"""
    vpc = appstream.VpcConfig(
        SecurityGroupIds=security_groups,
        SubnetIds=subnets
    )
    
    result = vpc.to_dict()
    
    # Lists should be preserved
    if security_groups:
        assert result.get('SecurityGroupIds') == security_groups
    if subnets:
        assert result.get('SubnetIds') == subnets


if __name__ == "__main__":
    # Run with pytest for better output
    pytest.main([__file__, "-v", "--tb=short"])