import json
from hypothesis import given, strategies as st, assume
import troposphere.s3outposts as s3o
import troposphere


@given(
    bucket_name=st.text(min_size=1, max_size=63),
    outpost_id=st.text(min_size=1, max_size=100)
)
def test_bucket_round_trip_from_dict_to_dict(bucket_name, outpost_id):
    """Test that Bucket.from_dict(obj.to_dict()) creates an equivalent object"""
    assume(bucket_name.strip() != "")
    assume(outpost_id.strip() != "")
    
    # Create bucket
    bucket1 = s3o.Bucket('TestBucket', 
                        BucketName=bucket_name,
                        OutpostId=outpost_id)
    
    # Convert to dict
    dict_repr = bucket1.to_dict()
    
    # Should be able to recreate from dict
    bucket2 = s3o.Bucket.from_dict('TestBucket2', dict_repr)
    dict_repr2 = bucket2.to_dict()
    
    # Dicts should be equal
    assert dict_repr == dict_repr2, f"Round-trip failed: {dict_repr} != {dict_repr2}"


@given(
    bucket_name=st.text(min_size=1, max_size=63),
    name=st.text(min_size=1, max_size=63),
    vpc_id=st.text(min_size=1, max_size=100)
)
def test_access_point_round_trip_from_dict_to_dict(bucket_name, name, vpc_id):
    """Test that AccessPoint.from_dict(obj.to_dict()) creates an equivalent object"""
    assume(bucket_name.strip() != "")
    assume(name.strip() != "")
    assume(vpc_id.strip() != "")
    
    # Create AccessPoint
    ap1 = s3o.AccessPoint('TestAP',
                         Bucket=bucket_name,
                         Name=name,
                         VpcConfiguration=s3o.VpcConfiguration(VpcId=vpc_id))
    
    # Convert to dict
    dict_repr = ap1.to_dict()
    
    # Should be able to recreate from dict
    ap2 = s3o.AccessPoint.from_dict('TestAP2', dict_repr)
    dict_repr2 = ap2.to_dict()
    
    # Dicts should be equal
    assert dict_repr == dict_repr2, f"Round-trip failed: {dict_repr} != {dict_repr2}"


@given(
    bucket_name=st.text(min_size=1, max_size=63),
    policy_doc=st.dictionaries(
        st.text(min_size=1, max_size=20),
        st.text(min_size=1, max_size=100),
        min_size=1,
        max_size=5
    )
)
def test_bucket_policy_round_trip_from_dict_to_dict(bucket_name, policy_doc):
    """Test that BucketPolicy.from_dict(obj.to_dict()) creates an equivalent object"""
    assume(bucket_name.strip() != "")
    
    # Create BucketPolicy
    bp1 = s3o.BucketPolicy('TestPolicy',
                          Bucket=bucket_name,
                          PolicyDocument=policy_doc)
    
    # Convert to dict
    dict_repr = bp1.to_dict()
    
    # Should be able to recreate from dict
    bp2 = s3o.BucketPolicy.from_dict('TestPolicy2', dict_repr)
    dict_repr2 = bp2.to_dict()
    
    # Dicts should be equal
    assert dict_repr == dict_repr2, f"Round-trip failed: {dict_repr} != {dict_repr2}"


@given(
    outpost_id=st.text(min_size=1, max_size=100),
    sg_id=st.text(min_size=1, max_size=100),
    subnet_id=st.text(min_size=1, max_size=100)
)
def test_endpoint_round_trip_from_dict_to_dict(outpost_id, sg_id, subnet_id):
    """Test that Endpoint.from_dict(obj.to_dict()) creates an equivalent object"""
    assume(outpost_id.strip() != "")
    assume(sg_id.strip() != "")
    assume(subnet_id.strip() != "")
    
    # Create Endpoint
    ep1 = s3o.Endpoint('TestEndpoint',
                      OutpostId=outpost_id,
                      SecurityGroupId=sg_id,
                      SubnetId=subnet_id)
    
    # Convert to dict
    dict_repr = ep1.to_dict()
    
    # Should be able to recreate from dict
    ep2 = s3o.Endpoint.from_dict('TestEndpoint2', dict_repr)
    dict_repr2 = ep2.to_dict()
    
    # Dicts should be equal
    assert dict_repr == dict_repr2, f"Round-trip failed: {dict_repr} != {dict_repr2}"


@given(
    bucket_name=st.text(min_size=1, max_size=63),
    outpost_id=st.text(min_size=1, max_size=100),
    tag_keys=st.lists(st.text(min_size=1, max_size=50), min_size=1, max_size=10),
    tag_values=st.lists(st.text(min_size=1, max_size=100), min_size=1, max_size=10)
)
def test_json_round_trip_with_tags(bucket_name, outpost_id, tag_keys, tag_values):
    """Test JSON serialization round-trip with Tags"""
    assume(bucket_name.strip() != "")
    assume(outpost_id.strip() != "")
    assume(len(tag_keys) == len(tag_values))
    assume(all(k.strip() != "" for k in tag_keys))
    
    # Create bucket with tags
    tags = troposphere.Tags(**{k: v for k, v in zip(tag_keys, tag_values)})
    bucket1 = s3o.Bucket('TestBucket', 
                        BucketName=bucket_name,
                        OutpostId=outpost_id,
                        Tags=tags)
    
    # Convert to JSON and back
    json_str = bucket1.to_json()
    parsed = json.loads(json_str)
    
    # Should be able to recreate from parsed JSON
    bucket2 = s3o.Bucket.from_dict('TestBucket2', parsed)
    
    # Convert both to dict and compare
    dict1 = bucket1.to_dict()
    dict2 = bucket2.to_dict()
    
    assert dict1 == dict2, f"JSON round-trip failed: {dict1} != {dict2}"


@given(st.data())
def test_validate_returns_none_for_incomplete_objects(data):
    """Test that validate() returns None even for incomplete objects missing required fields"""
    # Test various incomplete objects
    test_cases = [
        s3o.Bucket('TestBucket'),  # Missing BucketName and OutpostId
        s3o.Bucket('TestBucket', BucketName='test'),  # Missing OutpostId
        s3o.AccessPoint('TestAP'),  # Missing all required fields
        s3o.BucketPolicy('TestPolicy'),  # Missing all required fields
        s3o.Endpoint('TestEndpoint'),  # Missing all required fields
    ]
    
    for obj in test_cases:
        result = obj.validate()
        assert result is None, f"validate() should return None but returned {result} for {type(obj).__name__}"