import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, assume, strategies as st, settings, example
import troposphere.codecommit as codecommit
from troposphere import AWSHelperFn, Template
import json
import re


# Edge Case 1: Test trigger validation with AWSHelperFn mixed with regular events
class MockAWSHelperFn(AWSHelperFn):
    def to_dict(self):
        return {"Ref": "TestRef"}


def test_trigger_with_awshelper():
    """Test trigger with AWSHelperFn in events"""
    helper = MockAWSHelperFn()
    
    # Test with only AWSHelperFn
    trigger = codecommit.Trigger(
        Name="TestTrigger",
        DestinationArn="arn:aws:sns:us-east-1:123456789012:MyTopic",
        Events=helper
    )
    
    # Should not raise during validation since AWSHelperFn bypasses validation
    trigger.validate()
    
    # Test with list containing AWSHelperFn
    trigger2 = codecommit.Trigger(
        Name="TestTrigger",
        DestinationArn="arn:aws:sns:us-east-1:123456789012:MyTopic",
        Events=[helper]
    )
    trigger2.validate()


# Edge Case 2: Test repository title validation
@given(st.text(min_size=0, max_size=100))
def test_repository_title_validation(title):
    """Repository title must be alphanumeric"""
    valid_pattern = re.compile(r"^[a-zA-Z0-9]+$")
    is_valid = bool(title and valid_pattern.match(title))
    
    try:
        repo = codecommit.Repository(
            title,
            RepositoryName="TestRepo"
        )
        # If creation succeeds, title should be valid
        assert is_valid, f"Expected invalid title '{title}' to raise error"
    except ValueError as e:
        # If it fails, title should be invalid
        assert not is_valid, f"Expected valid title '{title}' not to raise error"
        assert "not alphanumeric" in str(e)


# Edge Case 3: Test trigger with mixed valid and "all" events
def test_trigger_all_with_valid_events():
    """Specific test for 'all' mixed with other valid events"""
    # This should fail
    trigger = codecommit.Trigger(
        Name="TestTrigger",
        DestinationArn="arn:aws:sns:us-east-1:123456789012:MyTopic",
        Events=["all", "createReference"]
    )
    
    try:
        trigger.validate()
        assert False, "Should have raised ValueError for 'all' with other events"
    except ValueError as e:
        assert "all must be used alone" in str(e)


# Edge Case 4: Test with duplicate events
def test_trigger_duplicate_events():
    """Test trigger with duplicate events"""
    trigger = codecommit.Trigger(
        Name="TestTrigger",
        DestinationArn="arn:aws:sns:us-east-1:123456789012:MyTopic",
        Events=["createReference", "createReference", "deleteReference"]
    )
    
    # Should pass validation (duplicates not explicitly forbidden)
    trigger.validate()
    dict_repr = trigger.to_dict()
    assert dict_repr["Events"] == ["createReference", "createReference", "deleteReference"]


# Edge Case 5: Test S3 with empty strings
@given(
    st.one_of(st.just(""), st.text(min_size=1, max_size=50)),
    st.one_of(st.just(""), st.text(min_size=1, max_size=50))
)
def test_s3_empty_strings(bucket, key):
    """Test S3 with empty bucket or key"""
    # Both bucket and key are required, but what if they're empty strings?
    s3 = codecommit.S3(Bucket=bucket, Key=key)
    dict_repr = s3.to_dict()
    
    # Empty strings should be preserved
    assert dict_repr["Bucket"] == bucket
    assert dict_repr["Key"] == key


# Edge Case 6: Test Repository with Triggers containing "all" event alone
def test_repository_with_all_trigger():
    """Test Repository with trigger using 'all' event correctly"""
    trigger = codecommit.Trigger(
        Name="AllTrigger",
        DestinationArn="arn:aws:sns:us-east-1:123456789012:MyTopic",
        Events=["all"]
    )
    
    repo = codecommit.Repository(
        "MyRepo",
        RepositoryName="TestRepo",
        Triggers=[trigger]
    )
    
    # Should work fine
    dict_repr = repo.to_dict()
    assert dict_repr["Properties"]["Triggers"][0]["Events"] == ["all"]


# Edge Case 7: Test Code without required S3
def test_code_missing_s3():
    """Code requires S3 property"""
    try:
        code = codecommit.Code(BranchName="main")
        code.to_dict()
        assert False, "Should have raised error for missing S3"
    except (ValueError, TypeError) as e:
        # Expected to fail
        pass


# Edge Case 8: Test nested object validation in Repository
@given(
    st.text(min_size=1, max_size=50).filter(lambda x: x.isalnum()),
    st.lists(
        st.sampled_from(["all", "createReference", "deleteReference", "updateReference"]),
        min_size=1,
        max_size=4
    )
)
def test_repository_with_triggers_validation(repo_name, events):
    """Repository with triggers should validate nested triggers"""
    trigger = codecommit.Trigger(
        Name="TestTrigger",
        DestinationArn="arn:aws:sns:us-east-1:123456789012:MyTopic",
        Events=events
    )
    
    repo = codecommit.Repository(
        "MyRepo",
        RepositoryName=repo_name,
        Triggers=[trigger]
    )
    
    try:
        # This should trigger validation of nested objects
        dict_repr = repo.to_dict()
        
        # If successful, check constraints
        if "all" in events:
            assert len(events) == 1, "'all' should be alone"
    except ValueError as e:
        # Should only fail if 'all' is with other events
        assert "all" in events and len(events) > 1


# Edge Case 9: Test very long strings
@given(
    st.text(min_size=1000, max_size=5000),
    st.text(min_size=1000, max_size=5000)
)
@settings(max_examples=10)
def test_s3_long_strings(bucket, key):
    """Test S3 with very long bucket and key names"""
    s3 = codecommit.S3(Bucket=bucket, Key=key)
    dict_repr = s3.to_dict()
    
    # Long strings should be preserved
    assert dict_repr["Bucket"] == bucket
    assert dict_repr["Key"] == key
    
    # Round-trip should work
    s3_restored = codecommit.S3._from_dict(**dict_repr)
    assert s3.to_dict() == s3_restored.to_dict()


# Edge Case 10: Test Repository with all optional properties
@given(
    st.text(min_size=1, max_size=50).filter(lambda x: x.isalnum()),
    st.text(min_size=0, max_size=1000),
    st.text(min_size=0, max_size=100),
    st.lists(st.text(min_size=1, max_size=50), min_size=0, max_size=3)
)
def test_repository_all_properties(repo_name, description, kms_key, branches):
    """Test Repository with all optional properties"""
    repo = codecommit.Repository(
        "MyRepo",
        RepositoryName=repo_name,
        RepositoryDescription=description if description else None,
        KmsKeyId=kms_key if kms_key else None
    )
    
    # Add Code if we have branches
    if branches:
        s3 = codecommit.S3(Bucket="test-bucket", Key="test-key")
        code = codecommit.Code(S3=s3, BranchName=branches[0])
        repo.Code = code
    
    dict_repr = repo.to_dict()
    
    # Check all properties are preserved
    assert dict_repr["Properties"]["RepositoryName"] == repo_name
    if description:
        assert dict_repr["Properties"]["RepositoryDescription"] == description
    if kms_key:
        assert dict_repr["Properties"]["KmsKeyId"] == kms_key
    if branches:
        assert dict_repr["Properties"]["Code"]["BranchName"] == branches[0]


# Edge Case 11: Test trigger with None events
def test_trigger_none_events():
    """Test trigger with None as events"""
    try:
        trigger = codecommit.Trigger(
            Name="TestTrigger",
            DestinationArn="arn:aws:sns:us-east-1:123456789012:MyTopic",
            Events=None
        )
        trigger.to_dict()
        assert False, "Should have raised error for None events"
    except (ValueError, TypeError, AttributeError):
        # Expected to fail
        pass


# Edge Case 12: Test special characters in trigger events
@given(st.text(min_size=1, max_size=50))
def test_trigger_special_chars_in_events(event_name):
    """Test trigger with special characters in event names"""
    assume(event_name not in ["all", "createReference", "deleteReference", "updateReference"])
    
    trigger = codecommit.Trigger(
        Name="TestTrigger",
        DestinationArn="arn:aws:sns:us-east-1:123456789012:MyTopic",
        Events=[event_name]
    )
    
    try:
        trigger.validate()
        # Should not succeed with invalid event names
        assert False, f"Should have raised error for invalid event: {event_name}"
    except ValueError as e:
        assert "invalid event" in str(e)


# Edge Case 13: Test Repository.from_dict with invalid structure
def test_repository_from_dict_invalid():
    """Test Repository.from_dict with various invalid structures"""
    
    # Test with missing required property
    try:
        repo = codecommit.Repository.from_dict("MyRepo", {})
        repo.to_dict()
        assert False, "Should have raised error for missing RepositoryName"
    except (ValueError, AttributeError):
        pass
    
    # Test with invalid nested structure
    try:
        repo = codecommit.Repository.from_dict("MyRepo", {
            "RepositoryName": "TestRepo",
            "Code": "invalid"  # Should be a dict
        })
        assert False, "Should have raised error for invalid Code structure"
    except (ValueError, AttributeError):
        pass


# Edge Case 14: Test trigger branches property
@given(st.lists(st.text(min_size=1, max_size=50), min_size=0, max_size=5))
def test_trigger_branches(branches):
    """Test trigger with various branch configurations"""
    trigger = codecommit.Trigger(
        Name="TestTrigger",
        DestinationArn="arn:aws:sns:us-east-1:123456789012:MyTopic",
        Events=["createReference"],
        Branches=branches if branches else None
    )
    
    trigger.validate()
    dict_repr = trigger.to_dict()
    
    if branches:
        assert dict_repr["Branches"] == branches
    else:
        assert "Branches" not in dict_repr or dict_repr["Branches"] is None


# Edge Case 15: Test custom data in trigger
@given(st.text(min_size=0, max_size=1000))
def test_trigger_custom_data(custom_data):
    """Test trigger with custom data of various sizes"""
    trigger = codecommit.Trigger(
        Name="TestTrigger",
        DestinationArn="arn:aws:sns:us-east-1:123456789012:MyTopic",
        Events=["createReference"],
        CustomData=custom_data if custom_data else None
    )
    
    trigger.validate()
    dict_repr = trigger.to_dict()
    
    if custom_data:
        assert dict_repr["CustomData"] == custom_data