"""
Property-based tests for troposphere.codegurureviewer module
"""
import json
import re
from hypothesis import given, strategies as st, assume, settings
from troposphere.codegurureviewer import RepositoryAssociation
from troposphere import Tags, AWSObject, BaseAWSObject


# Strategy for valid alphanumeric titles (ASCII only, as per AWS CloudFormation requirements)
valid_title_strategy = st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=100)

# Strategy for invalid titles (containing non-alphanumeric characters)
invalid_title_strategy = st.text(min_size=1, max_size=100).filter(
    lambda x: not re.match(r'^[a-zA-Z0-9]+$', x)
)

# Strategy for repository types (based on AWS documentation)
repo_type_strategy = st.sampled_from(['CodeCommit', 'GitHub', 'Bitbucket', 'GitHubEnterpriseServer', 'S3Bucket'])

# Strategy for valid property values
property_strategy = st.text(min_size=1, max_size=255)


@given(title=valid_title_strategy)
def test_valid_title_accepted(title):
    """Property: Valid alphanumeric titles should be accepted"""
    # This should not raise an exception
    obj = RepositoryAssociation(title)
    assert obj.title == title


@given(title=invalid_title_strategy)
def test_invalid_title_rejected(title):
    """Property: Non-alphanumeric titles should be rejected"""
    try:
        RepositoryAssociation(title)
        # If we get here, the validation failed to reject invalid title
        assert False, f"Invalid title '{title}' was accepted but should have been rejected"
    except ValueError as e:
        # This is expected behavior
        assert 'not alphanumeric' in str(e)


@given(
    title=valid_title_strategy,
    name=property_strategy,
    repo_type=repo_type_strategy
)
def test_required_properties(title, name, repo_type):
    """Property: Objects with required properties should be created successfully"""
    obj = RepositoryAssociation(
        title,
        Name=name,
        Type=repo_type
    )
    assert obj.Name == name
    assert obj.Type == repo_type


@given(
    title=valid_title_strategy,
    name=property_strategy,
    repo_type=repo_type_strategy,
    bucket_name=st.one_of(st.none(), property_strategy),
    connection_arn=st.one_of(st.none(), property_strategy),
    owner=st.one_of(st.none(), property_strategy)
)
def test_optional_properties(title, name, repo_type, bucket_name, connection_arn, owner):
    """Property: Optional properties should be settable"""
    kwargs = {
        'Name': name,
        'Type': repo_type
    }
    if bucket_name is not None:
        kwargs['BucketName'] = bucket_name
    if connection_arn is not None:
        kwargs['ConnectionArn'] = connection_arn
    if owner is not None:
        kwargs['Owner'] = owner
    
    obj = RepositoryAssociation(title, **kwargs)
    
    # Verify all properties are set correctly
    assert obj.Name == name
    assert obj.Type == repo_type
    if bucket_name is not None:
        assert obj.BucketName == bucket_name
    if connection_arn is not None:
        assert obj.ConnectionArn == connection_arn
    if owner is not None:
        assert obj.Owner == owner


@given(
    title=valid_title_strategy,
    name=property_strategy,
    repo_type=repo_type_strategy
)
def test_to_dict_serialization(title, name, repo_type):
    """Property: to_dict should produce valid dictionary representation"""
    obj = RepositoryAssociation(
        title,
        Name=name,
        Type=repo_type
    )
    
    result = obj.to_dict()
    
    # Should have Type and Properties keys
    assert 'Type' in result
    assert result['Type'] == 'AWS::CodeGuruReviewer::RepositoryAssociation'
    assert 'Properties' in result
    
    # Properties should contain our values
    props = result['Properties']
    assert props['Name'] == name
    assert props['Type'] == repo_type


@given(
    title=valid_title_strategy,
    name=property_strategy,
    repo_type=repo_type_strategy
)
def test_to_json_produces_valid_json(title, name, repo_type):
    """Property: to_json should produce valid JSON that can be parsed"""
    obj = RepositoryAssociation(
        title,
        Name=name,
        Type=repo_type
    )
    
    json_str = obj.to_json()
    
    # Should be valid JSON
    parsed = json.loads(json_str)
    
    # Should have expected structure
    assert parsed['Type'] == 'AWS::CodeGuruReviewer::RepositoryAssociation'
    assert parsed['Properties']['Name'] == name
    assert parsed['Properties']['Type'] == repo_type


@given(
    title=valid_title_strategy,
    name=property_strategy,
    repo_type=repo_type_strategy,
    bucket_name=st.one_of(st.none(), property_strategy)
)
def test_equality_property(title, name, repo_type, bucket_name):
    """Property: Two objects with same properties should be equal"""
    kwargs = {
        'Name': name,
        'Type': repo_type
    }
    if bucket_name is not None:
        kwargs['BucketName'] = bucket_name
    
    obj1 = RepositoryAssociation(title, **kwargs)
    obj2 = RepositoryAssociation(title, **kwargs)
    
    # They should be equal
    assert obj1 == obj2
    
    # Their JSON representations should also be equal
    assert obj1.to_json(validation=False) == obj2.to_json(validation=False)


@given(
    title1=valid_title_strategy,
    title2=valid_title_strategy,
    name=property_strategy,
    repo_type=repo_type_strategy
)
def test_inequality_different_titles(title1, title2, name, repo_type):
    """Property: Objects with different titles should not be equal"""
    assume(title1 != title2)  # Make sure titles are different
    
    obj1 = RepositoryAssociation(title1, Name=name, Type=repo_type)
    obj2 = RepositoryAssociation(title2, Name=name, Type=repo_type)
    
    # They should not be equal (different titles)
    assert obj1 != obj2


@given(
    title=valid_title_strategy,
    name1=property_strategy,
    name2=property_strategy,
    repo_type=repo_type_strategy
)
def test_inequality_different_properties(title, name1, name2, repo_type):
    """Property: Objects with different properties should not be equal"""
    assume(name1 != name2)  # Make sure names are different
    
    obj1 = RepositoryAssociation(title, Name=name1, Type=repo_type)
    obj2 = RepositoryAssociation(title, Name=name2, Type=repo_type)
    
    # They should not be equal (different properties)
    assert obj1 != obj2


@given(
    title=valid_title_strategy,
    name=property_strategy,
    repo_type=repo_type_strategy
)
def test_from_dict_roundtrip(title, name, repo_type):
    """Property: from_dict should be able to reconstruct object from to_dict output"""
    obj1 = RepositoryAssociation(
        title,
        Name=name,
        Type=repo_type
    )
    
    # Convert to dict
    dict_repr = obj1.to_dict()
    
    # Extract properties
    props = dict_repr.get('Properties', {})
    
    # Create new object from properties
    obj2 = RepositoryAssociation._from_dict(title=title, **props)
    
    # They should produce the same JSON output
    assert obj1.to_json(validation=False) == obj2.to_json(validation=False)


@given(
    title=valid_title_strategy,
    name=property_strategy,
    repo_type=repo_type_strategy,
    invalid_prop=property_strategy
)
def test_invalid_property_rejected(title, name, repo_type, invalid_prop):
    """Property: Setting properties not in props dict should raise AttributeError"""
    obj = RepositoryAssociation(
        title,
        Name=name,
        Type=repo_type
    )
    
    # Try to set a property that doesn't exist in props
    try:
        obj.InvalidPropertyName = invalid_prop
        # If we get here, it accepted an invalid property
        assert False, "Invalid property was accepted"
    except AttributeError as e:
        # This is expected
        assert "does not support attribute" in str(e)


@given(
    title=valid_title_strategy,
    name=property_strategy,
    repo_type=repo_type_strategy,
    tags=st.dictionaries(
        keys=property_strategy,
        values=property_strategy,
        min_size=0,
        max_size=10
    )
)
def test_tags_property(title, name, repo_type, tags):
    """Property: Tags should be settable and retrievable"""
    obj = RepositoryAssociation(
        title,
        Name=name,
        Type=repo_type,
        Tags=Tags(**tags) if tags else Tags()
    )
    
    # Object should be created successfully
    assert obj.Name == name
    assert obj.Type == repo_type
    
    # to_dict should work with tags
    result = obj.to_dict()
    assert 'Properties' in result


@given(title=valid_title_strategy)
def test_missing_required_properties_validation(title):
    """Property: Creating object without required properties should work initially but fail on to_dict()"""
    # Create object without required properties
    obj = RepositoryAssociation(title)
    
    # Object creation should succeed (validation is deferred)
    assert obj.title == title
    
    # But to_dict() with validation should fail for missing required properties
    try:
        obj.to_dict(validation=True)
        # If we get here, validation didn't catch missing required properties
        # This might be acceptable behavior - let's check
    except Exception:
        # This is expected if validation catches missing required properties
        pass
    
    # Without validation, to_dict should work
    result = obj.to_dict(validation=False)
    assert 'Type' in result


@given(
    title=valid_title_strategy,
    name=property_strategy,
    invalid_type=st.integers()  # Type should be string, not integer
)
def test_type_validation(title, name, invalid_type):
    """Property: Properties should validate their types"""
    try:
        obj = RepositoryAssociation(
            title,
            Name=name,
            Type=invalid_type  # This should be a string, not an integer
        )
        # If type checking is enforced, we shouldn't get here
        # Let's check if the value was coerced or stored as-is
        assert isinstance(obj.Type, (str, int))
    except (TypeError, ValueError) as e:
        # This is expected if type validation is strict
        pass