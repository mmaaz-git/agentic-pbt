#!/usr/bin/env python3
import json
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyatlan_env/lib/python3.13/site-packages')

from hypothesis import assume, given, strategies as st, settings
from hypothesis.strategies import composite
import math
import pytest

# Import the modules we want to test
from pyatlan.pkg.models import CustomPackage, PackageDefinition, PullPolicy
from pyatlan.pkg.ui import UIStep
from pyatlan.pkg.utils import validate_multiselect, validate_connection, validate_connector_and_connection
from pyatlan.pkg.widgets import UIElementWithEnum
from pyatlan.model.enums import AtlanConnectorType


# Strategy for valid package IDs - must match expected format
@composite
def package_ids(draw):
    """Generate valid package IDs that follow the expected format."""
    namespace = draw(st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=20))
    name = draw(st.text(alphabet="abcdefghijklmnopqrstuvwxyz-", min_size=1, max_size=30))
    return f"@{namespace}/{name}"


# Test 1: Package ID transformation is deterministic and preserves information
@given(st.text(min_size=1, max_size=100))
def test_package_id_to_name_transformation_deterministic(package_id):
    """Test that the package ID to name transformation is deterministic."""
    # Create a minimal CustomPackage to test the transformation
    package_data = {
        "package_id": package_id,
        "package_name": "Test Package",
        "description": "Test",
        "icon_url": "http://example.com/icon.png",
        "docs_url": "http://example.com/docs",
        "ui_config": {"steps": []},
        "container_image": "test:latest",
        "container_command": ["echo", "test"]
    }
    
    pkg1 = CustomPackage(**package_data)
    pkg2 = CustomPackage(**package_data)
    
    # The transformation should be deterministic
    assert pkg1.name == pkg2.name
    
    # The transformation should remove @ and replace / with -
    assert "@" not in pkg1.name
    assert "/" not in pkg1.name


# Test 2: UIStep title to ID transformation is deterministic
@given(st.text(min_size=1, max_size=100))
def test_ui_step_title_to_id_deterministic(title):
    """Test that UIStep title to ID transformation is deterministic."""
    step1 = UIStep(title=title, inputs={})
    step2 = UIStep(title=title, inputs={})
    
    # The transformation should be deterministic
    assert step1.id == step2.id
    
    # The ID should be lowercase and replace spaces with underscores
    assert step1.id == title.replace(" ", "_").lower()
    assert " " not in step1.id
    assert step1.id == step1.id.lower()


# Test 3: validate_multiselect handles JSON arrays correctly  
@given(st.lists(st.text(min_size=1, max_size=50), min_size=1, max_size=10))
def test_validate_multiselect_json_array(items):
    """Test that validate_multiselect correctly parses JSON array strings."""
    # Create a JSON array string
    json_str = json.dumps(items)
    
    # Validate it
    result = validate_multiselect(json_str)
    
    # Should get back the original list
    assert result == items
    assert isinstance(result, list)


# Test 4: validate_multiselect handles single values correctly
@given(st.text(min_size=1, max_size=100).filter(lambda x: not x.startswith("[")))
def test_validate_multiselect_single_value(value):
    """Test that validate_multiselect wraps single values in a list."""
    result = validate_multiselect(value)
    
    # Single values should be wrapped in a list
    assert result == [value]
    assert isinstance(result, list)
    assert len(result) == 1


# Test 5: validate_multiselect is idempotent for lists
@given(st.lists(st.text(min_size=1, max_size=50), min_size=0, max_size=10))
def test_validate_multiselect_idempotent_for_lists(items):
    """Test that validate_multiselect is idempotent when given a list."""
    result1 = validate_multiselect(items)
    result2 = validate_multiselect(result1)
    
    # Should be idempotent
    assert result1 == result2
    assert result1 == items


# Test 6: UIElementWithEnum maintains consistency between enum and enum_names
@given(st.dictionaries(
    st.text(min_size=1, max_size=20),
    st.text(min_size=1, max_size=50),
    min_size=1,
    max_size=10
))
def test_ui_element_enum_consistency(possible_values):
    """Test that UIElementWithEnum maintains consistency between enum lists."""
    element = UIElementWithEnum(
        type_="string",
        required=True,
        possible_values=possible_values
    )
    
    # The enum should contain the keys
    assert element.enum == list(possible_values.keys())
    
    # The enum_names should contain the values
    assert element.enum_names == list(possible_values.values())
    
    # They should have the same length
    assert len(element.enum) == len(element.enum_names)
    assert len(element.enum) == len(possible_values)
    
    # The possible_values should be preserved
    assert element.possible_values == possible_values


# Test 7: Package name property is consistent
@given(package_ids())
def test_package_name_property_consistency(package_id):
    """Test that the package name property returns consistent results."""
    package_data = {
        "package_id": package_id,
        "package_name": "Test Package",
        "description": "Test",
        "icon_url": "http://example.com/icon.png", 
        "docs_url": "http://example.com/docs",
        "ui_config": {"steps": []},
        "container_image": "test:latest",
        "container_command": ["echo", "test"]
    }
    
    pkg = CustomPackage(**package_data)
    
    # Multiple accesses should return the same value
    name1 = pkg.name
    name2 = pkg.name
    assert name1 == name2
    
    # The name should be derived from package_id
    expected = package_id.replace("@", "").replace("/", "-")
    assert pkg.name == expected


# Test 8: JSON serialization of CustomPackage produces valid JSON
@given(
    package_id=package_ids(),
    package_name=st.text(min_size=1, max_size=50),
    description=st.text(min_size=1, max_size=200)
)
def test_package_json_produces_valid_json(package_id, package_name, description):
    """Test that packageJSON produces valid JSON."""
    package_data = {
        "package_id": package_id,
        "package_name": package_name,
        "description": description,
        "icon_url": "http://example.com/icon.png",
        "docs_url": "http://example.com/docs",
        "ui_config": {"steps": []},
        "container_image": "test:latest",
        "container_command": ["echo", "test"]
    }
    
    pkg = CustomPackage(**package_data)
    json_str = pkg.packageJSON
    
    # Should be valid JSON
    parsed = json.loads(json_str)
    
    # Should contain expected fields
    assert parsed["name"] == package_id
    assert parsed["description"] == description
    assert "version" in parsed
    assert "scripts" in parsed


# Test 9: validate_multiselect round-trip property
@given(st.lists(st.text(min_size=1, max_size=50), min_size=0, max_size=20))
def test_validate_multiselect_round_trip(items):
    """Test that JSON encoding and validate_multiselect form a round-trip."""
    # Convert to JSON and back
    json_str = json.dumps(items)
    result = validate_multiselect(json_str)
    
    # Should get back the original
    assert result == items
    
    # Second round trip
    json_str2 = json.dumps(result)
    result2 = validate_multiselect(json_str2)
    assert result2 == items


# Test 10: UIStep ID generation avoids collisions for different titles
@given(
    st.lists(
        st.text(min_size=1, max_size=30).filter(lambda x: x.strip()),
        min_size=2,
        max_size=5,
        unique=True
    )
)
def test_ui_step_id_uniqueness(titles):
    """Test that different titles produce different IDs (unless they differ only in case/spaces)."""
    steps = [UIStep(title=title, inputs={}) for title in titles]
    
    # Normalize titles to check for expected collisions
    normalized_titles = [t.replace(" ", "_").lower() for t in titles]
    
    # If normalized titles are unique, IDs should be unique
    if len(set(normalized_titles)) == len(normalized_titles):
        ids = [step.id for step in steps]
        assert len(set(ids)) == len(ids), f"IDs not unique: {ids}"