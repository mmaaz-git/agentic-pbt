#!/usr/bin/env python3
"""Run hypothesis property-based tests for troposphere.iottwinmaker."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings, example
from hypothesis.strategies import composite
import troposphere
from troposphere import iottwinmaker
from troposphere.validators.iottwinmaker import validate_listvalue, validate_nestedtypel
import traceback


# More intensive test for edge cases
@given(st.data())
@settings(max_examples=100)
def test_datavalue_multiple_fields(data):
    """Test DataValue with multiple fields set simultaneously."""
    # Draw multiple field values
    fields = {}
    
    # Randomly choose which fields to set
    if data.draw(st.booleans()):
        fields["BooleanValue"] = data.draw(st.booleans())
    if data.draw(st.booleans()):
        fields["DoubleValue"] = data.draw(st.floats(allow_nan=False, allow_infinity=False))
    if data.draw(st.booleans()):
        fields["IntegerValue"] = data.draw(st.integers())
    if data.draw(st.booleans()):
        fields["StringValue"] = data.draw(st.text(min_size=1))
    if data.draw(st.booleans()):
        fields["Expression"] = data.draw(st.text(min_size=1))
    
    # Skip if no fields were chosen
    if not fields:
        return
    
    # Create DataValue with multiple fields
    dv = iottwinmaker.DataValue(**fields)
    dv_dict = dv.to_dict()
    
    # All fields should be preserved
    for key, value in fields.items():
        assert key in dv_dict, f"Field {key} missing from to_dict()"
        assert dv_dict[key] == value, f"Field {key} value mismatch"


@given(
    title=st.text(min_size=1),
    entity_name=st.text(min_size=1),
    workspace_id=st.text(min_size=1)
)
@settings(max_examples=100)
def test_entity_edge_cases(title, entity_name, workspace_id):
    """Test Entity with various edge case inputs."""
    # Skip invalid titles
    if not title.replace(" ", "").replace("\t", "").replace("\n", "").isalnum():
        return
    
    # Remove whitespace from title to make it valid
    valid_title = ''.join(c for c in title if c.isalnum())
    if not valid_title:
        return
    
    try:
        entity = iottwinmaker.Entity(
            valid_title,
            EntityName=entity_name,
            WorkspaceId=workspace_id
        )
        entity_dict = entity.to_dict(validation=False)
        
        # Check properties are preserved
        props = entity_dict["Properties"]
        assert props["EntityName"] == entity_name
        assert props["WorkspaceId"] == workspace_id
    except ValueError as e:
        # Title validation might fail for some edge cases
        if "not alphanumeric" in str(e):
            pass  # Expected for invalid titles
        else:
            raise


@given(
    component_name=st.text(min_size=1),
    component_type_id=st.text(min_size=1),
    description=st.one_of(st.none(), st.text())
)
@settings(max_examples=100)
def test_component_properties(component_name, component_type_id, description):
    """Test Component with various property combinations."""
    kwargs = {
        "ComponentName": component_name,
        "ComponentTypeId": component_type_id
    }
    
    if description is not None:
        kwargs["Description"] = description
    
    component = iottwinmaker.Component(**kwargs)
    comp_dict = component.to_dict(validation=False)
    
    # Verify all set properties are preserved
    assert comp_dict["ComponentName"] == component_name
    assert comp_dict["ComponentTypeId"] == component_type_id
    if description is not None:
        assert comp_dict["Description"] == description


@given(
    group_type=st.text(min_size=1),
    property_names=st.lists(st.text(min_size=1), min_size=0, max_size=10)
)
@settings(max_examples=100)
def test_property_group(group_type, property_names):
    """Test PropertyGroup with various inputs."""
    pg = iottwinmaker.PropertyGroup(
        GroupType=group_type,
        PropertyNames=property_names
    )
    
    pg_dict = pg.to_dict(validation=False)
    
    assert pg_dict["GroupType"] == group_type
    assert pg_dict["PropertyNames"] == property_names


@given(
    target_component=st.one_of(st.none(), st.text(min_size=1)),
    target_entity=st.one_of(st.none(), st.text(min_size=1))
)
@settings(max_examples=100) 
def test_relationship_value(target_component, target_entity):
    """Test RelationshipValue with optional fields."""
    kwargs = {}
    if target_component is not None:
        kwargs["TargetComponentName"] = target_component
    if target_entity is not None:
        kwargs["TargetEntityId"] = target_entity
    
    if kwargs:  # Only create if at least one field is set
        rv = iottwinmaker.RelationshipValue(**kwargs)
        rv_dict = rv.to_dict(validation=False)
        
        for key, value in kwargs.items():
            assert rv_dict[key] == value


@given(
    extends_from=st.lists(st.text(min_size=1), min_size=0, max_size=5),
    is_singleton=st.booleans()
)
@settings(max_examples=100)
def test_component_type_extends(extends_from, is_singleton):
    """Test ComponentType with ExtendsFrom list."""
    ct = iottwinmaker.ComponentType(
        "TestComponent",
        ComponentTypeId="comp-123",
        WorkspaceId="workspace-123",
        ExtendsFrom=extends_from,
        IsSingleton=is_singleton
    )
    
    ct_dict = ct.to_dict(validation=False)
    props = ct_dict["Properties"]
    
    if extends_from:
        assert props["ExtendsFrom"] == extends_from
    assert props["IsSingleton"] == is_singleton


# Test for potential bugs with empty strings
@given(st.just(""))
@example("")  # Force testing empty string
def test_empty_string_handling(empty_str):
    """Test how empty strings are handled in required fields."""
    # Empty strings in required fields might cause issues
    try:
        entity = iottwinmaker.Entity(
            "TestEntity",
            EntityName=empty_str,  # Empty string for required field
            WorkspaceId="workspace-123"
        )
        # If this doesn't raise an error, it might be a bug
        # as empty string might not be a valid EntityName
        entity_dict = entity.to_dict(validation=False)
        # Check if empty string is preserved
        assert entity_dict["Properties"]["EntityName"] == empty_str
    except Exception:
        # Expected to fail with empty string
        pass


# Test boolean validator edge cases
def test_boolean_validator_edge_cases():
    """Test the boolean validator with various inputs."""
    from troposphere.validators import boolean
    
    # Test valid boolean-like values
    assert boolean(True) == True
    assert boolean(False) == False
    assert boolean(1) == True
    assert boolean(0) == False
    assert boolean("true") == True
    assert boolean("false") == False
    assert boolean("True") == True
    assert boolean("False") == False
    
    # Test string "1" and "0" - undocumented but in code
    assert boolean("1") == True
    assert boolean("0") == False
    
    # Test invalid values
    try:
        boolean(2)  # Not a valid boolean value
        assert False, "Should have raised ValueError"
    except ValueError:
        pass
    
    try:
        boolean("yes")  # Not a valid boolean string
        assert False, "Should have raised ValueError"
    except ValueError:
        pass


def test_double_validator_edge_cases():
    """Test the double validator with edge cases."""
    from troposphere.validators import double
    
    # Test valid doubles
    assert double(3.14) == 3.14
    assert double(0) == 0
    assert double(-1.5) == -1.5
    assert double("3.14") == "3.14"  # Strings that can be converted
    
    # Test invalid values
    try:
        double("not_a_number")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "not a valid double" in str(e)
    
    try:
        double(None)
        assert False, "Should have raised ValueError"
    except (ValueError, TypeError):
        pass


def test_integer_validator_edge_cases():
    """Test the integer validator with edge cases."""
    from troposphere.validators import integer
    
    # Test valid integers
    assert integer(42) == 42
    assert integer(0) == 0
    assert integer(-1) == -1
    assert integer("42") == "42"  # Strings that can be converted
    
    # Test invalid values
    try:
        integer("not_a_number")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "not a valid integer" in str(e)
    
    try:
        integer(3.14)  # Float should work if it can be converted
        # This might not raise an error, depending on implementation
    except ValueError:
        pass


def main():
    """Run all hypothesis tests."""
    print("=" * 60)
    print("Running Hypothesis Property-Based Tests")
    print("=" * 60)
    
    all_passed = True
    
    # Run property tests
    tests = [
        test_datavalue_multiple_fields,
        test_entity_edge_cases,
        test_component_properties,
        test_property_group,
        test_relationship_value,
        test_component_type_extends,
        test_empty_string_handling,
    ]
    
    for test_func in tests:
        print(f"\nRunning {test_func.__name__}...")
        try:
            # Run hypothesis test multiple times
            test_func()
            print(f"✓ {test_func.__name__} passed")
        except AssertionError as e:
            print(f"✗ {test_func.__name__} failed: {e}")
            traceback.print_exc()
            all_passed = False
        except Exception as e:
            print(f"✗ {test_func.__name__} error: {e}")
            traceback.print_exc()
            all_passed = False
    
    # Run edge case tests
    edge_tests = [
        test_boolean_validator_edge_cases,
        test_double_validator_edge_cases,
        test_integer_validator_edge_cases,
    ]
    
    for test_func in edge_tests:
        print(f"\nRunning {test_func.__name__}...")
        try:
            test_func()
            print(f"✓ {test_func.__name__} passed")
        except AssertionError as e:
            print(f"✗ {test_func.__name__} failed: {e}")
            traceback.print_exc()
            all_passed = False
        except Exception as e:
            print(f"✗ {test_func.__name__} error: {e}")
            traceback.print_exc()
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ All hypothesis tests passed!")
    else:
        print("❌ Some tests failed!")
    print("=" * 60)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())