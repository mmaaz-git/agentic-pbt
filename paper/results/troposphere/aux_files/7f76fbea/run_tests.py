#!/usr/bin/env python3
"""Run the property-based tests for troposphere.iottwinmaker."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
from hypothesis.strategies import composite
import troposphere
from troposphere import iottwinmaker
from troposphere.validators.iottwinmaker import validate_listvalue, validate_nestedtypel

# Run specific tests
def run_validate_listvalue_test():
    """Test validate_listvalue with invalid input."""
    print("Testing validate_listvalue with non-list input...")
    
    # Test with non-list
    try:
        validate_listvalue("not a list")
        print("ERROR: Should have raised TypeError for non-list")
        return False
    except TypeError as e:
        if "ListValue must be a list" in str(e):
            print("✓ Correctly raised TypeError for non-list input")
        else:
            print(f"ERROR: Unexpected error message: {e}")
            return False
    
    # Test with list of invalid items
    try:
        validate_listvalue([1, 2, 3])
        print("ERROR: Should have raised TypeError for list with integers")
        return False
    except TypeError as e:
        if "ListValue must contain DataValue or AWSHelperFn" in str(e):
            print("✓ Correctly raised TypeError for invalid list items")
        else:
            print(f"ERROR: Unexpected error message: {e}")
            return False
    
    return True

def run_datavalue_test():
    """Test DataValue field preservation."""
    print("\nTesting DataValue field preservation...")
    
    # Test boolean value
    dv1 = iottwinmaker.DataValue(BooleanValue=True)
    if dv1.to_dict()["BooleanValue"] != True:
        print("ERROR: BooleanValue not preserved")
        return False
    print("✓ BooleanValue preserved correctly")
    
    # Test double value
    dv2 = iottwinmaker.DataValue(DoubleValue=3.14)
    if dv2.to_dict()["DoubleValue"] != 3.14:
        print("ERROR: DoubleValue not preserved")
        return False
    print("✓ DoubleValue preserved correctly")
    
    # Test integer value
    dv3 = iottwinmaker.DataValue(IntegerValue=42)
    if dv3.to_dict()["IntegerValue"] != 42:
        print("ERROR: IntegerValue not preserved")
        return False
    print("✓ IntegerValue preserved correctly")
    
    # Test string value
    dv4 = iottwinmaker.DataValue(StringValue="test")
    if dv4.to_dict()["StringValue"] != "test":
        print("ERROR: StringValue not preserved")
        return False
    print("✓ StringValue preserved correctly")
    
    return True

def run_entity_test():
    """Test Entity creation and serialization."""
    print("\nTesting Entity creation and serialization...")
    
    entity = iottwinmaker.Entity(
        "TestEntity",
        EntityName="MyEntity",
        WorkspaceId="workspace-123"
    )
    
    entity_dict = entity.to_dict(validation=False)
    props = entity_dict["Properties"]
    
    if props["EntityName"] != "MyEntity":
        print(f"ERROR: EntityName not preserved: {props.get('EntityName')}")
        return False
    print("✓ EntityName preserved correctly")
    
    if props["WorkspaceId"] != "workspace-123":
        print(f"ERROR: WorkspaceId not preserved: {props.get('WorkspaceId')}")
        return False
    print("✓ WorkspaceId preserved correctly")
    
    if entity_dict["Type"] != "AWS::IoTTwinMaker::Entity":
        print(f"ERROR: Type not set correctly: {entity_dict.get('Type')}")
        return False
    print("✓ Type set correctly")
    
    return True

def run_required_property_test():
    """Test required property validation."""
    print("\nTesting required property validation...")
    
    # Test ComponentType with missing required property
    try:
        ct = iottwinmaker.ComponentType(
            "TestComponentType",
            ComponentTypeId="comp-123"
            # Missing WorkspaceId - required!
        )
        ct.to_dict()  # This should trigger validation
        print("ERROR: Should have raised ValueError for missing WorkspaceId")
        return False
    except ValueError as e:
        if "required" in str(e).lower():
            print(f"✓ Correctly raised ValueError for missing required property: {e}")
        else:
            print(f"ERROR: Unexpected error message: {e}")
            return False
    
    return True

def run_title_validation_test():
    """Test title validation for resources."""
    print("\nTesting title validation...")
    
    # Valid alphanumeric title should work
    try:
        workspace1 = iottwinmaker.Workspace(
            "ValidTitle123",
            Role="test-role",
            S3Location="s3://bucket/path",
            WorkspaceId="test-workspace"
        )
        workspace1.to_dict(validation=False)
        print("✓ Valid alphanumeric title accepted")
    except Exception as e:
        print(f"ERROR: Valid title rejected: {e}")
        return False
    
    # Invalid title with special characters should fail
    try:
        workspace2 = iottwinmaker.Workspace(
            "Invalid-Title!",
            Role="test-role", 
            S3Location="s3://bucket/path",
            WorkspaceId="test-workspace"
        )
        print("ERROR: Should have raised ValueError for invalid title")
        return False
    except ValueError as e:
        if "not alphanumeric" in str(e):
            print(f"✓ Correctly raised ValueError for invalid title: {e}")
        else:
            print(f"ERROR: Unexpected error message: {e}")
            return False
    
    return True

def run_list_property_test():
    """Test list property handling."""
    print("\nTesting list property handling...")
    
    # Valid list should work
    scene1 = iottwinmaker.Scene(
        "TestScene",
        SceneId="scene-123",
        ContentLocation="s3://bucket/scene",
        WorkspaceId="workspace-123",
        Capabilities=["capability1", "capability2"]
    )
    
    scene_dict = scene1.to_dict(validation=False)
    if scene_dict["Properties"]["Capabilities"] != ["capability1", "capability2"]:
        print("ERROR: Capabilities list not preserved")
        return False
    print("✓ Capabilities list preserved correctly")
    
    # Non-list should fail
    try:
        scene2 = iottwinmaker.Scene(
            "TestScene2",
            SceneId="scene-123",
            ContentLocation="s3://bucket/scene",
            WorkspaceId="workspace-123",
            Capabilities="not_a_list"
        )
        print("ERROR: Should have raised error for non-list Capabilities")
        return False
    except Exception:
        print("✓ Correctly raised error for non-list Capabilities")
    
    return True

def run_equality_test():
    """Test object equality and hash consistency."""
    print("\nTesting object equality and hash consistency...")
    
    # Create two identical entities
    entity1 = iottwinmaker.Entity(
        "Entity1",
        EntityName="TestEntity",
        WorkspaceId="workspace-123"
    )
    
    entity2 = iottwinmaker.Entity(
        "Entity1",  # Same title
        EntityName="TestEntity",  # Same properties
        WorkspaceId="workspace-123"
    )
    
    entity3 = iottwinmaker.Entity(
        "Entity2",  # Different title
        EntityName="TestEntity",
        WorkspaceId="workspace-123"
    )
    
    # Test equality
    if entity1 != entity2:
        print("ERROR: Identical entities should be equal")
        return False
    print("✓ Identical entities are equal")
    
    if entity1 == entity3:
        print("ERROR: Entities with different titles should not be equal")
        return False
    print("✓ Entities with different titles are not equal")
    
    # Test hash consistency
    if hash(entity1) != hash(entity2):
        print("ERROR: Equal objects should have equal hashes")
        return False
    print("✓ Equal objects have equal hashes")
    
    return True

def main():
    """Run all tests."""
    print("=" * 60)
    print("Running Property-Based Tests for troposphere.iottwinmaker")
    print("=" * 60)
    
    all_passed = True
    
    tests = [
        run_validate_listvalue_test,
        run_datavalue_test,
        run_entity_test,
        run_required_property_test,
        run_title_validation_test,
        run_list_property_test,
        run_equality_test
    ]
    
    for test in tests:
        try:
            if not test():
                all_passed = False
        except Exception as e:
            print(f"ERROR in {test.__name__}: {e}")
            import traceback
            traceback.print_exc()
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed!")
    print("=" * 60)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())