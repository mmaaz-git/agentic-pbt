#!/usr/bin/env python3
"""Property-based tests for troposphere.datasync module."""

import json
import sys
import traceback
from typing import Any, Dict, List, Type

from hypothesis import assume, given, settings, strategies as st

# Add the virtual environment to the path
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.datasync as datasync
from troposphere import AWSObject, AWSProperty, Tags


# Helper strategies
def alphanumeric_string():
    """Generate valid alphanumeric strings for titles."""
    return st.text(alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")), min_size=1, max_size=50)


def invalid_title_string():
    """Generate strings with non-alphanumeric characters."""
    return st.text(min_size=1, max_size=50).filter(
        lambda s: not s.replace(" ", "").isalnum() and len(s) > 0
    )


def get_datasync_classes():
    """Get all AWSObject and AWSProperty classes from datasync module."""
    classes = []
    for name in dir(datasync):
        obj = getattr(datasync, name)
        if isinstance(obj, type) and (issubclass(obj, AWSObject) or issubclass(obj, AWSProperty)):
            if obj not in (AWSObject, AWSProperty):
                classes.append(obj)
    return classes


def generate_valid_props(cls: Type) -> Dict[str, Any]:
    """Generate valid properties for a given class based on its props definition."""
    props = {}
    for prop_name, (prop_type, required) in cls.props.items():
        if required:
            # Generate minimal valid value based on type
            if prop_type == str:
                props[prop_name] = "test_value"
            elif prop_type == int:
                props[prop_name] = 42
            elif prop_type == bool:
                props[prop_name] = True
            elif isinstance(prop_type, list) and prop_type[0] == str:
                props[prop_name] = ["test_item"]
            elif isinstance(prop_type, type) and issubclass(prop_type, AWSProperty):
                # Recursively generate props for nested AWSProperty
                props[prop_name] = prop_type(**generate_valid_props(prop_type))
    return props


# Test 1: Title validation
@given(
    cls=st.sampled_from(get_datasync_classes()).filter(lambda c: issubclass(c, AWSObject)),
    title=invalid_title_string()
)
def test_title_validation_rejects_invalid(cls, title):
    """Test that non-alphanumeric titles are rejected."""
    assume(not title.isalnum())  # Ensure title is actually invalid
    
    try:
        obj = cls(title=title)
        # If no exception, check if validation happens on to_dict()
        obj.to_dict()
        # If we get here, validation didn't work
        assert False, f"Expected ValueError for invalid title '{title}' but none was raised"
    except ValueError as e:
        # Expected behavior
        assert "not alphanumeric" in str(e)
    except Exception as e:
        # Any other exception is unexpected
        assert False, f"Unexpected exception type: {type(e).__name__}: {e}"


# Test 2: Required property validation
@given(
    cls=st.sampled_from(get_datasync_classes())
)
def test_required_properties_validation(cls):
    """Test that missing required properties raise errors."""
    # Get required properties
    required_props = {k for k, (_, req) in cls.props.items() if req}
    
    if not required_props:
        # No required properties to test
        return
    
    # For AWSObject, we need a valid title
    if issubclass(cls, AWSObject):
        obj = cls(title="ValidTitle")
    else:
        obj = cls()
    
    # Should raise error when converting to dict with validation
    try:
        obj.to_dict(validation=True)
        # If no error, that's a bug
        assert False, f"Expected ValueError for missing required properties in {cls.__name__}"
    except ValueError as e:
        # Expected - should mention "required"
        assert "required" in str(e).lower()


# Test 3: Round-trip property for valid objects
@given(
    cls=st.sampled_from(get_datasync_classes()).filter(lambda c: issubclass(c, AWSObject)),
    title=alphanumeric_string()
)
@settings(max_examples=50)
def test_round_trip_property(cls, title):
    """Test that from_dict(to_dict()) preserves object state."""
    # Generate valid properties
    props = generate_valid_props(cls)
    
    # Create original object
    original = cls(title=title, **props)
    
    # Convert to dict
    dict_repr = original.to_dict(validation=False)
    
    # Extract properties from dict
    if "Properties" in dict_repr:
        props_dict = dict_repr["Properties"]
    else:
        props_dict = {}
    
    # Create new object from dict
    try:
        recreated = cls.from_dict(title, props_dict)
        
        # Compare the objects
        assert original == recreated, f"Round-trip failed for {cls.__name__}"
        
        # Also check that their dict representations are the same
        assert original.to_dict(validation=False) == recreated.to_dict(validation=False)
    except Exception as e:
        # Log the error for debugging
        print(f"Round-trip test failed for {cls.__name__}: {e}")
        print(f"Original dict: {dict_repr}")
        raise


# Test 4: Equality and hash consistency
@given(
    cls=st.sampled_from(get_datasync_classes()).filter(lambda c: issubclass(c, AWSObject)),
    title=alphanumeric_string()
)
@settings(max_examples=50)
def test_equality_and_hash_consistency(cls, title):
    """Test that equal objects have the same hash."""
    props = generate_valid_props(cls)
    
    # Create two identical objects
    obj1 = cls(title=title, **props)
    obj2 = cls(title=title, **props)
    
    # They should be equal
    assert obj1 == obj2, f"Identical {cls.__name__} objects are not equal"
    
    # Equal objects must have the same hash
    assert hash(obj1) == hash(obj2), f"Equal {cls.__name__} objects have different hashes"
    
    # Create an object with different title
    if title != "DifferentTitle":
        obj3 = cls(title="DifferentTitle", **props)
        assert obj1 != obj3, f"Objects with different titles should not be equal"
        # Different objects should (usually) have different hashes
        # Note: hash collisions are possible but unlikely
        if hash(obj1) == hash(obj3):
            print(f"Warning: Hash collision detected for {cls.__name__}")


# Test 5: Type validation
@given(
    cls=st.sampled_from(get_datasync_classes()).filter(lambda c: issubclass(c, AWSObject)),
    title=alphanumeric_string(),
    wrong_value=st.one_of(
        st.integers(),
        st.floats(allow_nan=False),
        st.booleans(),
        st.dictionaries(st.text(), st.text())
    )
)
@settings(max_examples=50)
def test_type_validation(cls, title, wrong_value):
    """Test that setting wrong types for string properties raises TypeError."""
    # Find a string property to test
    string_props = [(k, v) for k, v in cls.props.items() if v[0] == str and not v[1]]  # Optional string props
    
    if not string_props:
        return  # No string properties to test
    
    prop_name = string_props[0][0]
    
    # Skip if the wrong value happens to be a string
    if isinstance(wrong_value, str):
        return
    
    # Try to create object with wrong type
    try:
        obj = cls(title=title)
        setattr(obj, prop_name, wrong_value)
        # If no immediate error, check on to_dict
        obj.to_dict()
        
        # Some types might be coerced, so let's check what was actually stored
        stored_value = getattr(obj, prop_name, None)
        if type(stored_value) != type(wrong_value):
            # Type was coerced, which might be intentional
            return
        
        # If we get here and types match, that might be a bug
        assert False, f"Expected TypeError when setting {prop_name} to {type(wrong_value).__name__} in {cls.__name__}"
    except TypeError as e:
        # Expected behavior
        assert "expected" in str(e).lower()


# Test 6: JSON serialization doesn't crash
@given(
    cls=st.sampled_from(get_datasync_classes()).filter(lambda c: issubclass(c, AWSObject)),
    title=alphanumeric_string()
)
@settings(max_examples=50)
def test_json_serialization(cls, title):
    """Test that to_json() produces valid JSON."""
    props = generate_valid_props(cls)
    obj = cls(title=title, **props)
    
    # Should produce valid JSON
    json_str = obj.to_json(validation=False)
    
    # Should be valid JSON
    parsed = json.loads(json_str)
    assert isinstance(parsed, dict)
    
    # Should contain Type field for AWSObject
    if hasattr(cls, 'resource_type'):
        assert "Type" in parsed
        assert parsed["Type"] == cls.resource_type


if __name__ == "__main__":
    print("Running property-based tests for troposphere.datasync...")
    
    # Run all tests
    test_functions = [
        test_title_validation_rejects_invalid,
        test_required_properties_validation,
        test_round_trip_property,
        test_equality_and_hash_consistency,
        test_type_validation,
        test_json_serialization
    ]
    
    for test_func in test_functions:
        print(f"\nRunning {test_func.__name__}...")
        try:
            test_func()
            print(f"✓ {test_func.__name__} passed")
        except Exception as e:
            print(f"✗ {test_func.__name__} failed:")
            traceback.print_exc()