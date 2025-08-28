#!/usr/bin/env python3
"""Property-based tests for troposphere.launchwizard module"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import json
from hypothesis import given, strategies as st, assume, settings
import troposphere
from troposphere import launchwizard
from troposphere import Tags


# Strategy for valid AWS resource titles (alphanumeric only)
valid_titles = st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')), min_size=1, max_size=255)

# Strategy for invalid titles (contain non-alphanumeric)
invalid_titles = st.text(min_size=1, max_size=255).filter(
    lambda x: not x.isalnum()
)

# Strategy for tag dictionaries
tag_dict = st.dictionaries(
    keys=st.text(min_size=1, max_size=128),
    values=st.text(min_size=0, max_size=256),
    min_size=0,
    max_size=50
)


@given(title=invalid_titles)
def test_deployment_invalid_title_raises_error(title):
    """Test that Deployment with non-alphanumeric title raises ValueError"""
    assume(title)  # Skip empty strings
    try:
        deployment = launchwizard.Deployment(
            title,
            DeploymentPatternName="pattern",
            Name="name",
            WorkloadName="workload"
        )
        # If we get here, the validation didn't happen in __init__
        deployment.validate_title()
        assert False, f"Expected ValueError for title '{title}'"
    except ValueError as e:
        assert 'not alphanumeric' in str(e)


@given(title=valid_titles)
def test_deployment_valid_title_accepted(title):
    """Test that Deployment with alphanumeric title is accepted"""
    deployment = launchwizard.Deployment(
        title,
        DeploymentPatternName="pattern",
        Name="name",
        WorkloadName="workload"
    )
    # Should not raise
    deployment.validate_title()
    assert deployment.title == title


@given(tags=tag_dict)
def test_tags_sorting_with_string_keys(tags):
    """Test that Tags with string keys are sorted"""
    # Create Tags object
    tag_obj = Tags(**tags)
    
    # Convert to dict representation
    tag_list = tag_obj.to_dict()
    
    # Extract keys from the tag list
    keys_in_order = [tag['Key'] for tag in tag_list if isinstance(tag, dict)]
    
    # Check if keys are sorted
    if tags:  # Only check if we have tags
        assert keys_in_order == sorted(tags.keys())


@given(tags1=tag_dict, tags2=tag_dict)
def test_tags_concatenation_preserves_all_tags(tags1, tags2):
    """Test that Tags concatenation via + operator preserves all tags"""
    tag_obj1 = Tags(**tags1)
    tag_obj2 = Tags(**tags2)
    
    # Concatenate
    combined = tag_obj1 + tag_obj2
    
    # Get all tags
    combined_list = combined.to_dict()
    
    # Count tags
    expected_count = len(tags1) + len(tags2)
    actual_count = len([t for t in combined_list if isinstance(t, dict)])
    
    assert actual_count == expected_count


@given(title=valid_titles)
def test_deployment_missing_required_properties_fails_validation(title):
    """Test that Deployment without required properties fails validation"""
    # Create deployment with missing required properties
    deployment = launchwizard.Deployment(title)
    
    # Validation should fail
    try:
        deployment.to_dict(validation=True)
        assert False, "Expected ValueError for missing required properties"
    except ValueError as e:
        assert 'required' in str(e).lower()


@given(
    title=valid_titles,
    deployment_pattern=st.text(min_size=1, max_size=100),
    name=st.text(min_size=1, max_size=100),
    workload=st.text(min_size=1, max_size=100),
    specs=st.dictionaries(
        keys=st.text(min_size=1, max_size=50),
        values=st.text(min_size=1, max_size=100),
        max_size=10
    ).filter(lambda d: d),  # Ensure non-empty
    tags=tag_dict
)
def test_deployment_round_trip(title, deployment_pattern, name, workload, specs, tags):
    """Test that Deployment survives to_dict/from_dict round-trip"""
    # Create original deployment
    original = launchwizard.Deployment(
        title,
        DeploymentPatternName=deployment_pattern,
        Name=name,
        WorkloadName=workload,
        Specifications=specs if specs else None,
        Tags=Tags(**tags) if tags else None
    )
    
    # Convert to dict
    dict_repr = original.to_dict()
    
    # Extract properties
    props = dict_repr.get('Properties', {})
    
    # Create new deployment from dict
    restored = launchwizard.Deployment.from_dict(title, props)
    
    # Compare
    assert restored.title == original.title
    assert restored.DeploymentPatternName == original.DeploymentPatternName
    assert restored.Name == original.Name
    assert restored.WorkloadName == original.WorkloadName
    
    # Check optional properties if present
    if specs:
        assert restored.Specifications == original.Specifications
    if tags:
        # Tags comparison is more complex due to internal representation
        original_tags = original.to_dict()['Properties'].get('Tags', [])
        restored_tags = restored.to_dict()['Properties'].get('Tags', [])
        assert original_tags == restored_tags


@given(mixed_tags=st.dictionaries(
    keys=st.one_of(
        st.text(min_size=1, max_size=50),
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False)
    ),
    values=st.text(min_size=0, max_size=100),
    min_size=1,
    max_size=20
))
def test_tags_with_mixed_key_types(mixed_tags):
    """Test Tags behavior with non-string keys (should not sort)"""
    # Filter to ensure we have at least one non-string key
    has_non_string = any(not isinstance(k, str) for k in mixed_tags.keys())
    assume(has_non_string)
    
    tag_obj = Tags(mixed_tags)
    tag_list = tag_obj.to_dict()
    
    # With mixed types, tags should not be sorted
    # Just verify it doesn't crash and produces correct number of tags
    assert len(tag_list) == len(mixed_tags)


@given(st.data())
def test_empty_title_edge_case(data):
    """Test that empty title is handled correctly"""
    # Empty string title should fail validation
    try:
        deployment = launchwizard.Deployment(
            "",
            DeploymentPatternName="pattern",
            Name="name",
            WorkloadName="workload"
        )
        # Empty title should fail validation
        deployment.validate_title()
        assert False, "Expected ValueError for empty title"
    except ValueError as e:
        assert 'not alphanumeric' in str(e)