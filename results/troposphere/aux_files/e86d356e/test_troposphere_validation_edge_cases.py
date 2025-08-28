#!/usr/bin/env python3
"""Test for additional validation edge cases in troposphere."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings, note
import troposphere.cassandra as cassandra
from troposphere import AWSHelperFn, Ref


# Test 1: Properties with AWSHelperFn values (CloudFormation intrinsic functions)
def test_awshelperfn_in_properties():
    """Test that AWSHelperFn values bypass type validation."""
    # Create a Ref (which is an AWSHelperFn)
    ref = Ref("SomeParameter")
    
    # These should accept Ref even though they expect specific types
    try:
        # KeyspaceName expects str but should accept Ref
        keyspace = cassandra.Keyspace(
            title="TestKeyspace",
            KeyspaceName=ref
        )
        result = keyspace.to_dict()
        assert "Ref" in str(result["Properties"]["KeyspaceName"])
        print("✓ Keyspace accepts Ref for KeyspaceName")
    except TypeError as e:
        print(f"✗ Keyspace rejects Ref for KeyspaceName: {e}")
    
    # Test with integer properties
    try:
        throughput = cassandra.ProvisionedThroughput(
            ReadCapacityUnits=ref,
            WriteCapacityUnits=ref
        )
        result = throughput.to_dict()
        print("✓ ProvisionedThroughput accepts Ref for capacity units")
    except TypeError as e:
        print(f"✗ ProvisionedThroughput rejects Ref: {e}")
    
    # Test with boolean properties
    try:
        keyspace = cassandra.Keyspace(
            title="TestKeyspace2",
            ClientSideTimestampsEnabled=ref
        )
        result = keyspace.to_dict()
        print("✓ Keyspace accepts Ref for boolean ClientSideTimestampsEnabled")
    except TypeError as e:
        print(f"✗ Keyspace rejects Ref for boolean: {e}")


# Test 2: Mixed types in lists
@given(st.lists(st.one_of(
    st.from_type(cassandra.Column),
    st.text(),
    st.integers(),
    st.none(),
), min_size=1, max_size=5))
def test_mixed_types_in_list_properties(mixed_list):
    """Test that list properties validate each element's type."""
    has_valid = any(isinstance(x, cassandra.Column) for x in mixed_list)
    has_invalid = any(not isinstance(x, (cassandra.Column, AWSHelperFn)) for x in mixed_list)
    
    if has_invalid:
        try:
            table = cassandra.Table(
                title="TestTable",
                KeyspaceName="test",
                PartitionKeyColumns=mixed_list
            )
            result = table.to_dict()
            # If this succeeds with invalid types, that's unexpected
            note(f"Accepted mixed list with invalid types: {[type(x).__name__ for x in mixed_list]}")
        except (TypeError, AttributeError):
            pass  # Expected


# Test 3: Property that's both in props and attributes
def test_metadata_property():
    """Test handling of special attributes like Metadata."""
    # Metadata is in the attributes list, not props
    try:
        keyspace = cassandra.Keyspace(
            title="TestKeyspace",
            KeyspaceName="test",
            Metadata={"key": "value"}  # This is an attribute, not a property
        )
        result = keyspace.to_dict()
        # Metadata should be at the resource level, not in Properties
        assert "Metadata" in result
        assert result["Metadata"] == {"key": "value"}
        print("✓ Metadata handled correctly as attribute")
    except Exception as e:
        print(f"✗ Metadata handling failed: {e}")


# Test 4: DependsOn with object references
def test_depends_on_with_objects():
    """Test DependsOn attribute with object references."""
    keyspace1 = cassandra.Keyspace(
        title="Keyspace1",
        KeyspaceName="ks1"
    )
    
    keyspace2 = cassandra.Keyspace(
        title="Keyspace2", 
        KeyspaceName="ks2",
        DependsOn=keyspace1  # Should use keyspace1.title
    )
    
    result = keyspace2.to_dict()
    assert result.get("DependsOn") == "Keyspace1"
    print("✓ DependsOn correctly extracts title from object")
    
    # Test with list of dependencies
    keyspace3 = cassandra.Keyspace(
        title="Keyspace3",
        KeyspaceName="ks3",
        DependsOn=[keyspace1, keyspace2]
    )
    
    result = keyspace3.to_dict()
    assert result.get("DependsOn") == ["Keyspace1", "Keyspace2"]
    print("✓ DependsOn handles list of objects")


# Test 5: Setting properties after construction
def test_property_mutation():
    """Test that properties can be modified after construction."""
    column = cassandra.Column(
        ColumnName="initial",
        ColumnType="text"
    )
    
    # Initial state
    result1 = column.to_dict()
    assert result1["ColumnName"] == "initial"
    
    # Modify property
    column.ColumnName = "modified"
    
    # Check it changed
    result2 = column.to_dict()
    assert result2["ColumnName"] == "modified"
    print("✓ Properties can be mutated after construction")
    
    # Try to set an invalid property
    try:
        column.InvalidProperty = "value"
        print("✗ Allowed setting invalid property")
    except AttributeError:
        print("✓ Correctly rejected invalid property")


# Test 6: Validation happens at right time
def test_validation_timing():
    """Test when validation actually occurs."""
    # Create with invalid OrderBy but don't serialize yet
    column = cassandra.Column(ColumnName="test", ColumnType="text")
    
    try:
        # This might not validate immediately
        clustering = cassandra.ClusteringKeyColumn(
            Column=column,
            OrderBy="INVALID"
        )
        print("✓ Construction succeeded with invalid OrderBy (lazy validation)")
        
        # Validation should happen here
        result = clustering.to_dict()
        print("✗ to_dict() succeeded with invalid OrderBy")
    except (ValueError, TypeError) as e:
        if "construction" in str(e).lower():
            print("✓ Validation happened at construction time")
        else:
            print("✓ Validation happened at serialization time")


# Test 7: Properties with wrong number of arguments
def test_wrong_constructor_args():
    """Test error handling for wrong constructor arguments."""
    try:
        # Column requires ColumnName and ColumnType
        column = cassandra.Column("name", "type")  # Positional args
        print("✗ Accepted positional arguments")
    except TypeError:
        print("✓ Correctly rejected positional arguments")
    
    try:
        # Extra unknown argument
        column = cassandra.Column(
            ColumnName="test",
            ColumnType="text",
            UnknownArg="value"
        )
        print("✗ Accepted unknown argument")
    except AttributeError:
        print("✓ Correctly rejected unknown argument")


# Test 8: Empty string handling
@given(st.sampled_from(["", " ", "  ", "\t", "\n"]))
def test_empty_and_whitespace_strings(value):
    """Test handling of empty and whitespace-only strings."""
    # Empty strings might be valid CloudFormation values
    try:
        keyspace = cassandra.Keyspace(
            title="Test",
            KeyspaceName=value
        )
        result = keyspace.to_dict()
        assert result["Properties"]["KeyspaceName"] == value
        note(f"Accepted {repr(value)} as KeyspaceName")
    except (ValueError, TypeError):
        note(f"Rejected {repr(value)} as KeyspaceName")


if __name__ == "__main__":
    print("Testing AWSHelperFn in properties...")
    test_awshelperfn_in_properties()
    print("\nTesting Metadata property...")
    test_metadata_property()
    print("\nTesting DependsOn with objects...")
    test_depends_on_with_objects()
    print("\nTesting property mutation...")
    test_property_mutation()
    print("\nTesting validation timing...")
    test_validation_timing()
    print("\nTesting constructor arguments...")
    test_wrong_constructor_args()
    
    print("\nRunning property-based tests...")
    import pytest
    pytest.main([__file__, "-v", "--tb=short", "-k", "test_mixed_types|test_empty"])