#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages/')

import troposphere.forecast as forecast

def test_schema_mutation_bug():
    """Demonstrate potential mutation bug in Schema"""
    print("Testing Schema mutation bug...")
    
    # Create a list of attributes
    attrs_list = [
        forecast.AttributesItems(AttributeName="attr1", AttributeType="string")
    ]
    
    # Create a Schema with this list
    schema = forecast.Schema(Attributes=attrs_list)
    
    # Get the initial state
    dict_before = schema.to_dict()
    print(f"Before mutation: {dict_before}")
    print(f"Number of attributes: {len(dict_before['Attributes'])}")
    
    # Now modify the original list
    attrs_list.append(
        forecast.AttributesItems(AttributeName="attr2", AttributeType="integer")
    )
    attrs_list.append(
        forecast.AttributesItems(AttributeName="attr3", AttributeType="float")
    )
    
    # Get the state after modifying the original list
    dict_after = schema.to_dict()
    print(f"\nAfter mutation: {dict_after}")
    print(f"Number of attributes: {len(dict_after['Attributes'])}")
    
    # Check if they're different
    if dict_before != dict_after:
        print("\n❌ BUG FOUND: Schema stores a reference to the list, not a copy!")
        print("   Modifying the original list affects the Schema object.")
        return True
    else:
        print("\n✓ No bug: Schema properly copies the list")
        return False

def test_dataset_schema_mutation():
    """Test if the same issue affects Dataset"""
    print("\n\nTesting Dataset-Schema mutation...")
    
    # Create attributes list
    attrs_list = [
        forecast.AttributesItems(AttributeName="item_id", AttributeType="string"),
        forecast.AttributesItems(AttributeName="timestamp", AttributeType="timestamp")
    ]
    
    # Create Schema
    schema = forecast.Schema(Attributes=attrs_list)
    
    # Create Dataset with the Schema
    dataset = forecast.Dataset(
        "TestDataset",
        DatasetName="test_dataset",
        DatasetType="TARGET_TIME_SERIES",
        Domain="RETAIL",
        Schema=schema
    )
    
    # Get initial state
    dict_before = dataset.to_dict()
    attrs_before = dict_before["Properties"]["Schema"]["Attributes"]
    print(f"Dataset attributes before: {len(attrs_before)}")
    
    # Modify the original attributes list
    attrs_list.append(
        forecast.AttributesItems(AttributeName="value", AttributeType="float")
    )
    
    # Check Dataset again
    dict_after = dataset.to_dict()
    attrs_after = dict_after["Properties"]["Schema"]["Attributes"]
    print(f"Dataset attributes after modifying original list: {len(attrs_after)}")
    
    if len(attrs_before) != len(attrs_after):
        print("❌ BUG: Dataset is affected by mutations to the original attributes list!")
        return True
    else:
        print("✓ Dataset is not affected by list mutations")
        return False

def test_nested_mutation_in_dataset():
    """Test if nested objects can be mutated after Dataset creation"""
    print("\n\nTesting nested object mutation in Dataset...")
    
    # Create Schema
    schema = forecast.Schema(
        Attributes=[
            forecast.AttributesItems(AttributeName="original", AttributeType="string")
        ]
    )
    
    # Create Dataset
    dataset = forecast.Dataset(
        "TestDataset",
        DatasetName="test",
        DatasetType="TARGET_TIME_SERIES",
        Domain="RETAIL",
        Schema=schema
    )
    
    # Get initial state
    dict_before = dataset.to_dict()
    print(f"Before: {dict_before['Properties']['Schema']}")
    
    # Try to mutate the schema's attributes directly
    schema.Attributes.append(
        forecast.AttributesItems(AttributeName="added_later", AttributeType="integer")
    )
    
    # Check if Dataset is affected
    dict_after = dataset.to_dict()
    print(f"After: {dict_after['Properties']['Schema']}")
    
    if dict_before != dict_after:
        print("❌ BUG: Dataset's Schema can be mutated after creation!")
        return True
    else:
        print("✓ Dataset's Schema is protected from mutation")
        return False

def create_minimal_reproduction():
    """Create minimal reproduction script for the bug"""
    print("\n\n" + "="*60)
    print("MINIMAL REPRODUCTION SCRIPT")
    print("="*60)
    
    print("""
# Minimal script to reproduce the mutation bug:

import troposphere.forecast as forecast

# Create a list of attributes
attrs = [forecast.AttributesItems(AttributeName="attr1", AttributeType="string")]

# Create Schema with this list
schema = forecast.Schema(Attributes=attrs)

# Initial state
print(f"Before: {len(schema.to_dict()['Attributes'])} attributes")

# Modify the original list
attrs.append(forecast.AttributesItems(AttributeName="attr2", AttributeType="integer"))

# Check state after mutation
print(f"After: {len(schema.to_dict()['Attributes'])} attributes")

# If the numbers differ, the Schema stores a reference instead of a copy!
""")

if __name__ == "__main__":
    bug1 = test_schema_mutation_bug()
    bug2 = test_dataset_schema_mutation()
    bug3 = test_nested_mutation_in_dataset()
    
    if bug1 or bug2 or bug3:
        create_minimal_reproduction()
        print("\n⚠️  BUGS FOUND - See details above")
    else:
        print("\n✅ No mutation bugs found")