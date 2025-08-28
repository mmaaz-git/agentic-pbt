import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, assume, strategies as st, settings
import troposphere.codecommit as codecommit
from troposphere import AWSHelperFn
import json


# Property 1: Trigger event validation - "all" must be used alone
@given(st.lists(st.sampled_from(["all", "createReference", "deleteReference", "updateReference"]), min_size=1, max_size=4))
def test_trigger_events_all_alone(events):
    """If 'all' is in events, it must be the only element"""
    trigger = codecommit.Trigger(
        Name="TestTrigger",
        DestinationArn="arn:aws:sns:us-east-1:123456789012:MyTopic",
        Events=events
    )
    
    try:
        trigger.validate()
        # If validation passes, check the constraint
        if "all" in events:
            assert len(events) == 1, f"'all' event should be alone but events={events}"
    except ValueError as e:
        # If validation fails, it should only fail when 'all' is with others
        if "all" in events and len(events) > 1:
            assert "all must be used alone" in str(e)
        else:
            # Re-raise if it's a different validation error
            raise


# Property 2: Invalid events should raise errors
@given(st.lists(st.text(min_size=1, max_size=20), min_size=1, max_size=3))
def test_trigger_invalid_events(events):
    """Invalid events should raise ValueError"""
    valid_events = ["all", "createReference", "deleteReference", "updateReference"]
    
    # Filter out empty strings
    events = [e for e in events if e]
    if not events:
        return  # Skip empty lists
    
    has_invalid = any(e not in valid_events for e in events)
    
    trigger = codecommit.Trigger(
        Name="TestTrigger",
        DestinationArn="arn:aws:sns:us-east-1:123456789012:MyTopic",
        Events=events
    )
    
    try:
        trigger.validate()
        # If validation passes, all events should be valid
        assert not has_invalid, f"Expected validation error for events={events}"
    except ValueError as e:
        # If validation fails, there should be at least one invalid event
        if has_invalid:
            assert "invalid event" in str(e)
        else:
            # Re-raise if it's a different validation error
            raise


# Property 3: Required properties must be present
@given(
    st.booleans(),  # include Name
    st.booleans(),  # include DestinationArn
    st.booleans(),  # include Events
)
def test_trigger_required_properties(has_name, has_dest_arn, has_events):
    """Required properties must be present when creating and converting to dict"""
    kwargs = {}
    if has_name:
        kwargs["Name"] = "TestTrigger"
    if has_dest_arn:
        kwargs["DestinationArn"] = "arn:aws:sns:us-east-1:123456789012:MyTopic"
    if has_events:
        kwargs["Events"] = ["createReference"]
    
    try:
        trigger = codecommit.Trigger(**kwargs)
        result = trigger.to_dict()
        # If we got here, all required properties should be present
        assert has_name and has_dest_arn and has_events
    except (ValueError, TypeError) as e:
        # If it fails, at least one required property should be missing
        assert not (has_name and has_dest_arn and has_events)


# Property 4: Repository required properties
@given(
    st.booleans(),  # include RepositoryName
    st.text(min_size=1, max_size=50).filter(lambda x: x.replace("_", "").replace("-", "").isalnum() if x else False),  # Valid name
)
def test_repository_required_name(has_name, name):
    """Repository requires RepositoryName"""
    kwargs = {}
    if has_name:
        kwargs["RepositoryName"] = name
    
    try:
        repo = codecommit.Repository("MyRepo", **kwargs)
        result = repo.to_dict()
        # If we got here, name should be present
        assert has_name
    except (ValueError, TypeError) as e:
        # If it fails, name should be missing
        assert not has_name


# Property 5: S3 required properties
@given(
    st.booleans(),  # include Bucket
    st.booleans(),  # include Key
    st.text(min_size=1, max_size=30),  # bucket name
    st.text(min_size=1, max_size=30),  # key name
)
def test_s3_required_properties(has_bucket, has_key, bucket, key):
    """S3 requires both Bucket and Key"""
    kwargs = {}
    if has_bucket:
        kwargs["Bucket"] = bucket
    if has_key:
        kwargs["Key"] = key
    
    try:
        s3 = codecommit.S3(**kwargs)
        result = s3.to_dict()
        # If we got here, both should be present
        assert has_bucket and has_key
    except (ValueError, TypeError) as e:
        # If it fails, at least one should be missing
        assert not (has_bucket and has_key)


# Property 6: Round-trip serialization for S3
@given(
    st.text(min_size=1, max_size=50),  # bucket
    st.text(min_size=1, max_size=50),  # key
    st.one_of(st.none(), st.text(min_size=1, max_size=20))  # optional version
)
def test_s3_round_trip(bucket, key, version):
    """S3 to_dict and from_dict should preserve data"""
    kwargs = {"Bucket": bucket, "Key": key}
    if version is not None:
        kwargs["ObjectVersion"] = version
    
    s3_original = codecommit.S3(**kwargs)
    dict_repr = s3_original.to_dict()
    s3_restored = codecommit.S3._from_dict(**dict_repr)
    
    # Compare the dictionaries
    assert s3_original.to_dict() == s3_restored.to_dict()


# Property 7: Round-trip serialization for Repository with nested objects
@given(
    st.text(min_size=1, max_size=50).filter(lambda x: x.isalnum()),  # repo name
    st.one_of(st.none(), st.text(min_size=1, max_size=100)),  # description
    st.one_of(st.none(), st.text(min_size=1, max_size=50)),  # KMS key
)
def test_repository_round_trip(repo_name, description, kms_key):
    """Repository round-trip should preserve all properties"""
    kwargs = {"RepositoryName": repo_name}
    if description:
        kwargs["RepositoryDescription"] = description
    if kms_key:
        kwargs["KmsKeyId"] = kms_key
    
    repo_original = codecommit.Repository("TestRepo", **kwargs)
    dict_repr = repo_original.to_dict()
    
    # Extract just the Properties part for from_dict
    props = dict_repr.get("Properties", {})
    repo_restored = codecommit.Repository._from_dict("TestRepo", **props)
    
    # Compare the dictionaries
    assert repo_original.to_dict() == repo_restored.to_dict()


# Property 8: Trigger with all valid combinations
@given(
    st.lists(st.sampled_from(["createReference", "deleteReference", "updateReference"]), min_size=1, max_size=3, unique=True)
)
def test_trigger_valid_combinations(events):
    """Valid event combinations should work correctly"""
    trigger = codecommit.Trigger(
        Name="TestTrigger",
        DestinationArn="arn:aws:sns:us-east-1:123456789012:MyTopic",
        Events=events
    )
    
    # Should not raise any errors
    trigger.validate()
    dict_repr = trigger.to_dict()
    
    # Events should be preserved
    assert dict_repr["Events"] == events
    assert dict_repr["Name"] == "TestTrigger"
    assert dict_repr["DestinationArn"] == "arn:aws:sns:us-east-1:123456789012:MyTopic"


# Property 9: Edge case - empty events list
def test_trigger_empty_events():
    """Empty events list handling"""
    trigger = codecommit.Trigger(
        Name="TestTrigger",
        DestinationArn="arn:aws:sns:us-east-1:123456789012:MyTopic",
        Events=[]
    )
    
    # Empty list should pass validation (no invalid events)
    trigger.validate()
    dict_repr = trigger.to_dict()
    assert dict_repr["Events"] == []


# Property 10: Code with S3 reference
@given(
    st.text(min_size=1, max_size=50),  # bucket
    st.text(min_size=1, max_size=50),  # key
    st.one_of(st.none(), st.text(min_size=1, max_size=30))  # branch
)
def test_code_with_s3(bucket, key, branch):
    """Code requires S3 and optionally takes BranchName"""
    s3 = codecommit.S3(Bucket=bucket, Key=key)
    kwargs = {"S3": s3}
    if branch:
        kwargs["BranchName"] = branch
    
    code = codecommit.Code(**kwargs)
    dict_repr = code.to_dict()
    
    # S3 should be properly nested
    assert "S3" in dict_repr
    assert dict_repr["S3"]["Bucket"] == bucket
    assert dict_repr["S3"]["Key"] == key
    
    if branch:
        assert dict_repr["BranchName"] == branch