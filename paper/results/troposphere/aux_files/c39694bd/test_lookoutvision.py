#!/usr/bin/env python3
"""Property-based tests for troposphere.lookoutvision module."""

import json
import re
import sys
import string
from hypothesis import assume, given, strategies as st, settings

# Add troposphere to path
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import AWSObject
from troposphere.lookoutvision import Project


# Strategies for generating test data
# Valid alphanumeric titles (based on valid_names regex in troposphere/__init__.py)
valid_title_strategy = st.text(
    alphabet=string.ascii_letters + string.digits,
    min_size=1,
    max_size=255
).filter(lambda s: re.match(r"^[a-zA-Z0-9]+$", s))

# Invalid titles with special characters
invalid_title_strategy = st.text(min_size=1, max_size=255).filter(
    lambda s: not re.match(r"^[a-zA-Z0-9]+$", s)
)

# Valid project names
valid_project_name_strategy = st.text(min_size=1, max_size=255)


@given(
    title=valid_title_strategy,
    project_name=valid_project_name_strategy
)
def test_project_creation_with_valid_inputs(title, project_name):
    """Test that Project can be created with valid title and ProjectName."""
    project = Project(title, ProjectName=project_name)
    assert project.title == title
    assert project.ProjectName == project_name
    assert project.resource_type == "AWS::LookoutVision::Project"


@given(title=invalid_title_strategy)
def test_invalid_title_raises_value_error(title):
    """Test that invalid titles (non-alphanumeric) raise ValueError."""
    assume(title)  # Skip empty strings
    assume(not re.match(r"^[a-zA-Z0-9]+$", title))  # Ensure it's actually invalid
    
    try:
        project = Project(title, ProjectName="valid-name")
        assert False, f"Should have raised ValueError for title: {repr(title)}"
    except ValueError as e:
        assert 'not alphanumeric' in str(e)


@given(title=valid_title_strategy)
def test_required_property_validation(title):
    """Test that missing required ProjectName raises ValueError on validation."""
    project = Project(title)
    try:
        project.to_dict()  # This triggers validation
        assert False, "Should have raised ValueError for missing ProjectName"
    except ValueError as e:
        assert 'ProjectName' in str(e)
        assert 'required' in str(e)


@given(
    title=valid_title_strategy,
    project_name=valid_project_name_strategy
)
def test_to_dict_from_dict_round_trip(title, project_name):
    """Test that to_dict/from_dict is a proper round-trip."""
    # Create original project
    original = Project(title, ProjectName=project_name)
    
    # Convert to dict
    dict_repr = original.to_dict()
    
    # The dict should have the expected structure
    assert 'Type' in dict_repr
    assert dict_repr['Type'] == "AWS::LookoutVision::Project"
    assert 'Properties' in dict_repr
    assert 'ProjectName' in dict_repr['Properties']
    assert dict_repr['Properties']['ProjectName'] == project_name
    
    # Create new project from dict (using just Properties)
    restored = Project.from_dict(title, dict_repr['Properties'])
    
    # They should be equal
    assert original == restored
    assert original.title == restored.title
    assert original.ProjectName == restored.ProjectName


@given(
    title=valid_title_strategy,
    invalid_value=st.one_of(
        st.integers(),
        st.floats(allow_nan=False),
        st.lists(st.text()),
        st.dictionaries(st.text(), st.text()),
        st.booleans()
    )
)
def test_project_name_type_validation(title, invalid_value):
    """Test that ProjectName must be a string."""
    try:
        project = Project(title, ProjectName=invalid_value)
        # Type checking happens on attribute assignment
        # If we get here, check if the value was somehow accepted
        assert isinstance(invalid_value, str), f"Non-string value {type(invalid_value)} was accepted"
    except TypeError as e:
        # This is expected for non-string values
        assert "expected" in str(e).lower()


@given(
    title1=valid_title_strategy,
    title2=valid_title_strategy,
    project_name=valid_project_name_strategy
)
def test_equality_same_properties(title1, title2, project_name):
    """Test that two Projects with same properties are equal if titles match."""
    project1 = Project(title1, ProjectName=project_name)
    project2 = Project(title2, ProjectName=project_name)
    
    if title1 == title2:
        assert project1 == project2
        assert hash(project1) == hash(project2)
    else:
        assert project1 != project2


@given(
    title=valid_title_strategy,
    project_name1=valid_project_name_strategy,
    project_name2=valid_project_name_strategy
)
def test_equality_different_properties(title, project_name1, project_name2):
    """Test that two Projects with different properties are not equal."""
    project1 = Project(title, ProjectName=project_name1)
    project2 = Project(title, ProjectName=project_name2)
    
    if project_name1 == project_name2:
        assert project1 == project2
        assert hash(project1) == hash(project2)
    else:
        assert project1 != project2


@given(
    title=valid_title_strategy,
    project_name=valid_project_name_strategy
)
def test_json_serialization(title, project_name):
    """Test that Project can be serialized to and from JSON."""
    project = Project(title, ProjectName=project_name)
    
    # Convert to JSON
    json_str = project.to_json()
    
    # Parse back the JSON
    parsed = json.loads(json_str)
    
    # Check structure
    assert parsed['Type'] == "AWS::LookoutVision::Project"
    assert parsed['Properties']['ProjectName'] == project_name
    
    # Create new project from parsed data
    restored = Project.from_dict(title, parsed['Properties'])
    assert project == restored


@given(
    title=valid_title_strategy,
    project_name=valid_project_name_strategy
)
def test_no_validation_mode(title, project_name):
    """Test that no_validation() disables validation."""
    # Create project without required property
    project = Project(title)
    project.no_validation()
    
    # This should not raise even though ProjectName is missing
    result = project.to_dict(validation=False)
    assert 'Type' in result
    assert result['Type'] == "AWS::LookoutVision::Project"


@given(
    title=valid_title_strategy,
    project_name=valid_project_name_strategy,
    extra_attr=st.text(min_size=1, max_size=50).filter(lambda s: s != "ProjectName")
)
def test_invalid_attribute_raises_error(title, project_name, extra_attr):
    """Test that setting an unknown attribute raises AttributeError."""
    assume(extra_attr not in ["Properties", "Type", "title", "template", "Condition", 
                              "CreationPolicy", "DeletionPolicy", "DependsOn", 
                              "Metadata", "UpdatePolicy", "UpdateReplacePolicy",
                              "resource_type", "props", "propnames", "do_validation",
                              "properties", "resource", "attributes", "dictname"])
    
    project = Project(title, ProjectName=project_name)
    try:
        setattr(project, extra_attr, "some_value")
        assert False, f"Should have raised AttributeError for unknown attribute: {extra_attr}"
    except AttributeError as e:
        assert extra_attr in str(e)


@given(
    title=valid_title_strategy,
    project_name=valid_project_name_strategy
)
@settings(max_examples=100)
def test_ref_and_getatt_methods(title, project_name):
    """Test that ref() and get_att() methods work correctly."""
    project = Project(title, ProjectName=project_name)
    
    # Test ref() method
    ref = project.ref()
    ref_dict = ref.to_dict()
    assert ref_dict == {"Ref": title}
    
    # Test Ref (alias)
    ref2 = project.Ref()
    assert ref2.to_dict() == ref_dict
    
    # Test get_att() method
    attr = project.get_att("Arn")
    attr_dict = attr.to_dict()
    assert attr_dict == {"Fn::GetAtt": [title, "Arn"]}
    
    # Test GetAtt (alias)
    attr2 = project.GetAtt("Arn")
    assert attr2.to_dict() == attr_dict