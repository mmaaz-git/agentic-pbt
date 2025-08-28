"""
Additional edge case tests for troposphere.codegurureviewer
"""
from hypothesis import given, strategies as st, assume, settings
from troposphere.codegurureviewer import RepositoryAssociation
from troposphere import Tags
import json


# Test with empty strings and None values
@given(
    title=st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=100),
    name=st.one_of(st.just(''), st.text(min_size=1, max_size=255)),
    repo_type=st.sampled_from(['CodeCommit', 'GitHub', 'Bitbucket', 'GitHubEnterpriseServer', 'S3Bucket'])
)
def test_empty_name_property(title, name, repo_type):
    """Test if empty string is accepted for Name property"""
    obj = RepositoryAssociation(
        title,
        Name=name,
        Type=repo_type
    )
    # Empty string should be accepted as it's still a string
    assert obj.Name == name
    assert obj.Type == repo_type


@given(
    title=st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=100),
    name=st.text(min_size=1, max_size=255),
    repo_type=st.just('')
)
def test_empty_type_property(title, name, repo_type):
    """Test if empty string is accepted for Type property"""
    obj = RepositoryAssociation(
        title,
        Name=name,
        Type=repo_type
    )
    # Empty string should be accepted as it's still a string
    assert obj.Name == name
    assert obj.Type == repo_type


@given(
    title=st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=100),
    name=st.text(min_size=1, max_size=255)
)
def test_invalid_type_values(title, name):
    """Test validation of Type property with invalid values"""
    # Type is required and should be one of the valid repository types
    # Let's test with invalid values
    invalid_types = ['InvalidType', 'Random', 'NotARepo']
    
    for invalid_type in invalid_types:
        obj = RepositoryAssociation(
            title,
            Name=name,
            Type=invalid_type
        )
        # The object should accept any string for Type
        # AWS will validate this at deployment time
        assert obj.Type == invalid_type


@given(
    title=st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=100),
    very_long_name=st.text(min_size=1000, max_size=5000),
    repo_type=st.sampled_from(['CodeCommit', 'GitHub'])
)
@settings(max_examples=10)  # Reduce examples for performance
def test_very_long_strings(title, very_long_name, repo_type):
    """Test with very long string values"""
    obj = RepositoryAssociation(
        title,
        Name=very_long_name,
        Type=repo_type
    )
    assert obj.Name == very_long_name
    
    # Should be able to serialize even with very long strings
    json_str = obj.to_json()
    parsed = json.loads(json_str)
    assert parsed['Properties']['Name'] == very_long_name


@given(
    title=st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=100),
    name=st.text(min_size=1, max_size=255),
    repo_type=st.sampled_from(['CodeCommit', 'GitHub'])
)
def test_special_characters_in_values(title, name, repo_type):
    """Test property values with special characters"""
    # Add special characters to the name
    special_names = [
        name + '\n',  # newline
        name + '\t',  # tab
        name + '\r',  # carriage return
        '"' + name + '"',  # quotes
        name + '\\',  # backslash
        name + '\u0000' if '\u0000' not in name else name,  # null character
    ]
    
    for special_name in special_names:
        obj = RepositoryAssociation(
            title,
            Name=special_name,
            Type=repo_type
        )
        assert obj.Name == special_name
        
        # JSON serialization should handle special characters
        json_str = obj.to_json()
        parsed = json.loads(json_str)
        assert parsed['Properties']['Name'] == special_name


@given(
    title=st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=100)
)
def test_attribute_access_before_setting(title):
    """Test accessing attributes that haven't been set"""
    obj = RepositoryAssociation(title)
    
    # Accessing unset required properties should raise AttributeError
    try:
        _ = obj.Name
        assert False, "Should have raised AttributeError for unset Name"
    except AttributeError:
        pass  # Expected
    
    try:
        _ = obj.Type
        assert False, "Should have raised AttributeError for unset Type"
    except AttributeError:
        pass  # Expected
    
    # Accessing unset optional properties should also raise AttributeError
    try:
        _ = obj.BucketName
        assert False, "Should have raised AttributeError for unset BucketName"
    except AttributeError:
        pass  # Expected


@given(
    title=st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=100),
    name=st.text(min_size=1, max_size=255),
    repo_type=st.sampled_from(['CodeCommit', 'GitHub'])
)
def test_multiple_property_updates(title, name, repo_type):
    """Test updating properties multiple times"""
    obj = RepositoryAssociation(
        title,
        Name=name,
        Type=repo_type
    )
    
    # Update Name multiple times
    new_name1 = name + "_updated1"
    obj.Name = new_name1
    assert obj.Name == new_name1
    
    new_name2 = name + "_updated2"
    obj.Name = new_name2
    assert obj.Name == new_name2
    
    # Verify final state in JSON
    json_str = obj.to_json()
    parsed = json.loads(json_str)
    assert parsed['Properties']['Name'] == new_name2


@given(
    title1=st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=100),
    title2=st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=100),
    name=st.text(min_size=1, max_size=255),
    repo_type=st.sampled_from(['CodeCommit', 'GitHub'])
)
def test_hash_consistency(title1, title2, name, repo_type):
    """Test that hash is consistent for equal objects"""
    obj1 = RepositoryAssociation(title1, Name=name, Type=repo_type)
    obj2 = RepositoryAssociation(title1, Name=name, Type=repo_type)
    
    if obj1 == obj2:
        # Equal objects must have equal hashes
        assert hash(obj1) == hash(obj2)
    
    # Create object with different title
    obj3 = RepositoryAssociation(title2, Name=name, Type=repo_type)
    
    if obj1 != obj3:
        # Different objects might have different hashes (not required, but common)
        # We can't assert they're different as hash collisions are allowed
        pass


@given(
    title=st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=100),
    name=st.text(min_size=1, max_size=255),
    repo_type=st.sampled_from(['CodeCommit', 'GitHub']),
    metadata=st.dictionaries(st.text(min_size=1, max_size=50), st.text(min_size=1, max_size=100), min_size=0, max_size=5)
)
def test_metadata_attribute(title, name, repo_type, metadata):
    """Test setting Metadata attribute (CloudFormation attribute)"""
    obj = RepositoryAssociation(
        title,
        Name=name,
        Type=repo_type,
        Metadata=metadata
    )
    
    # Metadata should be stored in resource, not properties
    assert obj.Metadata == metadata
    
    # Check it appears in to_dict output
    result = obj.to_dict()
    if metadata:  # Only appears if non-empty
        assert result.get('Metadata') == metadata


@given(
    title=st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=100),
    name=st.text(min_size=1, max_size=255),
    repo_type=st.sampled_from(['CodeCommit', 'GitHub']),
    depends_on=st.lists(st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=50), min_size=0, max_size=3)
)
def test_depends_on_attribute(title, name, repo_type, depends_on):
    """Test setting DependsOn attribute"""
    obj = RepositoryAssociation(
        title,
        Name=name,
        Type=repo_type,
        DependsOn=depends_on
    )
    
    # DependsOn should be stored in resource
    assert obj.DependsOn == depends_on
    
    # Check it appears in to_dict output
    result = obj.to_dict()
    if depends_on:  # Only appears if non-empty
        assert result.get('DependsOn') == depends_on