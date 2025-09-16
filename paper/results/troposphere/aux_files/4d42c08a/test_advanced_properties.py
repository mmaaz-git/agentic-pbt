"""
Advanced property-based tests for troposphere.codegurureviewer
Testing for deeper properties and potential inconsistencies
"""
from hypothesis import given, strategies as st, assume, settings
from troposphere.codegurureviewer import RepositoryAssociation
from troposphere import Ref, GetAtt, Tags
import json
import copy


# Test reference and attribute functions
@given(
    title=st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=100),
    name=st.text(min_size=1, max_size=255),
    repo_type=st.sampled_from(['CodeCommit', 'GitHub'])
)
def test_ref_function(title, name, repo_type):
    """Test the ref() function returns correct CloudFormation reference"""
    obj = RepositoryAssociation(
        title,
        Name=name,
        Type=repo_type
    )
    
    # Test ref() method
    ref = obj.ref()
    assert isinstance(ref, Ref)
    
    # Test Ref() method (alias)
    ref2 = obj.Ref()
    assert isinstance(ref2, Ref)
    
    # Both should produce same result
    assert ref.to_dict() == ref2.to_dict()
    
    # Should reference the object's title
    ref_dict = ref.to_dict()
    assert 'Ref' in ref_dict
    assert ref_dict['Ref'] == title


@given(
    title=st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=100),
    name=st.text(min_size=1, max_size=255),
    repo_type=st.sampled_from(['CodeCommit', 'GitHub']),
    attribute=st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=50)
)
def test_get_att_function(title, name, repo_type, attribute):
    """Test the get_att() function for CloudFormation GetAtt"""
    obj = RepositoryAssociation(
        title,
        Name=name,
        Type=repo_type
    )
    
    # Test get_att() method
    att = obj.get_att(attribute)
    assert isinstance(att, GetAtt)
    
    # Test GetAtt() method (alias)
    att2 = obj.GetAtt(attribute)
    assert isinstance(att2, GetAtt)
    
    # Both should produce same result
    assert att.to_dict() == att2.to_dict()
    
    # Should reference the object and attribute
    att_dict = att.to_dict()
    assert 'Fn::GetAtt' in att_dict
    assert len(att_dict['Fn::GetAtt']) == 2
    assert att_dict['Fn::GetAtt'][0] == title
    assert att_dict['Fn::GetAtt'][1] == attribute


@given(
    title=st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=100),
    name=st.text(min_size=1, max_size=255),
    repo_type=st.sampled_from(['CodeCommit', 'GitHub'])
)
def test_no_validation_mode(title, name, repo_type):
    """Test that no_validation() disables validation"""
    obj = RepositoryAssociation(title)  # Missing required properties
    obj.no_validation()
    
    # Should be able to convert to dict without validation
    result = obj.to_dict(validation=False)
    assert 'Type' in result
    
    # Test that validation is indeed disabled
    assert not obj.do_validation


@given(
    title=st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=100),
    name=st.text(min_size=1, max_size=255),
    repo_type=st.sampled_from(['CodeCommit', 'GitHub']),
    bucket_name=st.text(min_size=1, max_size=100)
)
def test_deepcopy_object(title, name, repo_type, bucket_name):
    """Test that objects can be deep copied correctly"""
    obj1 = RepositoryAssociation(
        title,
        Name=name,
        Type=repo_type,
        BucketName=bucket_name
    )
    
    # Deep copy the object
    obj2 = copy.deepcopy(obj1)
    
    # They should be equal but not the same object
    assert obj1 == obj2
    assert obj1 is not obj2
    
    # Modifying one shouldn't affect the other
    obj2.Name = name + "_modified"
    assert obj1.Name != obj2.Name
    assert obj1.Name == name
    assert obj2.Name == name + "_modified"


@given(
    title=st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=100),
    name=st.text(min_size=1, max_size=255),
    repo_type=st.sampled_from(['CodeCommit', 'GitHub']),
    deletion_policy=st.sampled_from(['Delete', 'Retain', 'Snapshot'])
)
def test_deletion_policy_attribute(title, name, repo_type, deletion_policy):
    """Test DeletionPolicy CloudFormation attribute"""
    obj = RepositoryAssociation(
        title,
        Name=name,
        Type=repo_type,
        DeletionPolicy=deletion_policy
    )
    
    # DeletionPolicy should be in resource, not properties
    assert obj.DeletionPolicy == deletion_policy
    
    result = obj.to_dict()
    assert result.get('DeletionPolicy') == deletion_policy
    assert 'DeletionPolicy' not in result.get('Properties', {})


@given(
    title=st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=100),
    name=st.text(min_size=1, max_size=255),
    repo_type=st.sampled_from(['CodeCommit', 'GitHub']),
    condition=st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=50)
)
def test_condition_attribute(title, name, repo_type, condition):
    """Test Condition CloudFormation attribute"""
    obj = RepositoryAssociation(
        title,
        Name=name,
        Type=repo_type,
        Condition=condition
    )
    
    # Condition should be in resource, not properties
    assert obj.Condition == condition
    
    result = obj.to_dict()
    assert result.get('Condition') == condition
    assert 'Condition' not in result.get('Properties', {})


@given(
    title=st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=100),
    name=st.text(min_size=1, max_size=255),
    repo_type=st.sampled_from(['CodeCommit', 'GitHub'])
)
def test_json_indentation_parameter(title, name, repo_type):
    """Test to_json with different indentation settings"""
    obj = RepositoryAssociation(
        title,
        Name=name,
        Type=repo_type
    )
    
    # Test different indentations
    json2 = obj.to_json(indent=2)
    json4 = obj.to_json(indent=4)
    json_none = obj.to_json(indent=None)
    
    # All should parse to same object
    parsed2 = json.loads(json2)
    parsed4 = json.loads(json4)
    parsed_none = json.loads(json_none)
    
    assert parsed2 == parsed4 == parsed_none
    
    # But formatting should be different
    assert len(json2) != len(json4)  # Different indentation
    assert '\n' in json2 and '\n' in json4  # Should have newlines
    assert '\n' not in json_none  # No newlines with indent=None


@given(
    title=st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=100),
    name=st.text(min_size=1, max_size=255),
    repo_type=st.sampled_from(['CodeCommit', 'GitHub'])
)
def test_json_sort_keys_parameter(title, name, repo_type):
    """Test to_json with sort_keys parameter"""
    obj = RepositoryAssociation(
        title,
        Name=name,
        Type=repo_type,
        BucketName="bucket",
        Owner="owner",
        ConnectionArn="arn"
    )
    
    # Get JSON with and without sorted keys
    json_sorted = obj.to_json(sort_keys=True)
    json_unsorted = obj.to_json(sort_keys=False)
    
    # Both should parse to same object
    parsed_sorted = json.loads(json_sorted)
    parsed_unsorted = json.loads(json_unsorted)
    
    assert parsed_sorted == parsed_unsorted
    
    # In sorted version, Properties should come before Type alphabetically
    assert json_sorted.index('"Properties"') < json_sorted.index('"Type"')


@given(
    title=st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=100),
    name=st.text(min_size=1, max_size=255),
    repo_type=st.sampled_from(['CodeCommit', 'GitHub']),
    tags_dict=st.dictionaries(
        st.text(min_size=1, max_size=50),
        st.text(min_size=1, max_size=100),
        min_size=1,
        max_size=5
    )
)
def test_tags_multiple_formats(title, name, repo_type, tags_dict):
    """Test Tags can be created in multiple ways"""
    # Test Tags created from kwargs
    obj1 = RepositoryAssociation(
        title,
        Name=name,
        Type=repo_type,
        Tags=Tags(**tags_dict)
    )
    
    # Test Tags created from dict argument
    obj2 = RepositoryAssociation(
        title + "2",
        Name=name,
        Type=repo_type,
        Tags=Tags(tags_dict)
    )
    
    # Both should produce Tags in the output
    result1 = obj1.to_dict()
    result2 = obj2.to_dict()
    
    assert 'Tags' in result1['Properties']
    assert 'Tags' in result2['Properties']
    
    # Tags should be list of Key/Value pairs in CloudFormation format
    tags1 = result1['Properties']['Tags']
    tags2 = result2['Properties']['Tags']
    
    assert isinstance(tags1, list)
    assert isinstance(tags2, list)
    assert len(tags1) == len(tags_dict)
    assert len(tags2) == len(tags_dict)