#!/usr/bin/env python3
"""Investigate the bugs found in DataValue and DataType."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import iottwinmaker
import json


def investigate_datavalue_listvalue_bug():
    """Investigate the DataValue ListValue bug in detail."""
    print("=" * 60)
    print("INVESTIGATING: DataValue ListValue Bug")
    print("=" * 60)
    
    # Create simple DataValues
    dv1 = iottwinmaker.DataValue(StringValue="test1")
    dv2 = iottwinmaker.DataValue(IntegerValue=42)
    
    print("\n1. Creating DataValue with ListValue...")
    dv_list = iottwinmaker.DataValue(ListValue=[dv1, dv2])
    
    print("\n2. Calling to_dict()...")
    dv_dict = dv_list.to_dict()
    print(f"Result: {dv_dict}")
    
    print("\n3. Checking ListValue field...")
    list_value = dv_dict.get("ListValue")
    print(f"ListValue type: {type(list_value)}")
    print(f"ListValue content: {list_value}")
    
    if list_value is None:
        print("\n❌ BUG CONFIRMED: ListValue is None instead of a list!")
        
        # Try to access the property directly
        print("\n4. Trying to access ListValue property directly...")
        try:
            direct_value = dv_list.ListValue
            print(f"Direct access type: {type(direct_value)}")
            print(f"Direct access value: {direct_value}")
        except Exception as e:
            print(f"Direct access failed: {e}")
        
        # Check internal properties
        print("\n5. Checking internal properties dict...")
        if hasattr(dv_list, 'properties'):
            print(f"Properties: {dv_list.properties}")
        
        return True
    else:
        print("✓ ListValue is correctly set as a list")
        return False


def investigate_datatype_nestedtype_bug():
    """Investigate the DataType NestedType bug in detail."""
    print("\n" + "=" * 60)
    print("INVESTIGATING: DataType NestedType Bug")
    print("=" * 60)
    
    # Create inner DataType
    inner_dt = iottwinmaker.DataType(Type="STRING")
    print("\n1. Created inner DataType with Type='STRING'")
    inner_dict = inner_dt.to_dict()
    print(f"Inner DataType dict: {inner_dict}")
    
    # Create outer DataType with NestedType
    print("\n2. Creating outer DataType with NestedType...")
    outer_dt = iottwinmaker.DataType(NestedType=inner_dt)
    
    print("\n3. Calling to_dict() on outer DataType...")
    outer_dict = outer_dt.to_dict()
    print(f"Result: {outer_dict}")
    
    print("\n4. Checking NestedType field...")
    nested_type = outer_dict.get("NestedType")
    print(f"NestedType type: {type(nested_type)}")
    print(f"NestedType content: {nested_type}")
    
    if nested_type is None:
        print("\n❌ BUG CONFIRMED: NestedType is None instead of a dict!")
        
        # Try to access the property directly
        print("\n5. Trying to access NestedType property directly...")
        try:
            direct_value = outer_dt.NestedType
            print(f"Direct access type: {type(direct_value)}")
            print(f"Direct access value: {direct_value}")
        except Exception as e:
            print(f"Direct access failed: {e}")
        
        # Check internal properties
        print("\n6. Checking internal properties dict...")
        if hasattr(outer_dt, 'properties'):
            print(f"Properties: {outer_dt.properties}")
        
        return True
    else:
        print("✓ NestedType is correctly set")
        return False


def create_minimal_reproduction():
    """Create minimal reproduction scripts for the bugs."""
    print("\n" + "=" * 60)
    print("MINIMAL REPRODUCTION SCRIPTS")
    print("=" * 60)
    
    print("\n### Bug 1: DataValue ListValue returns None ###")
    print("""
from troposphere import iottwinmaker

# Create DataValues to put in list
dv1 = iottwinmaker.DataValue(StringValue="test")
dv2 = iottwinmaker.DataValue(IntegerValue=42)

# Create DataValue with ListValue
dv_list = iottwinmaker.DataValue(ListValue=[dv1, dv2])

# Convert to dict - ListValue becomes None
result = dv_list.to_dict()
print(f"Result: {result}")
print(f"ListValue is None: {result.get('ListValue') is None}")  # True - BUG!
""")
    
    print("\n### Bug 2: DataType NestedType returns None ###")
    print("""
from troposphere import iottwinmaker

# Create inner DataType
inner_dt = iottwinmaker.DataType(Type="STRING")

# Create outer DataType with NestedType
outer_dt = iottwinmaker.DataType(NestedType=inner_dt)

# Convert to dict - NestedType becomes None
result = outer_dt.to_dict()
print(f"Result: {result}")
print(f"NestedType is None: {result.get('NestedType') is None}")  # True - BUG!
""")


def main():
    """Run bug investigation."""
    bug1_found = investigate_datavalue_listvalue_bug()
    bug2_found = investigate_datatype_nestedtype_bug()
    
    if bug1_found or bug2_found:
        create_minimal_reproduction()
        print("\n" + "=" * 60)
        print("🐛 BUGS FOUND!")
        print("=" * 60)
        
        if bug1_found:
            print("1. DataValue.ListValue returns None in to_dict()")
        if bug2_found:
            print("2. DataType.NestedType returns None in to_dict()")
        
        return 1
    else:
        print("\n✅ No bugs found in this investigation")
        return 0


if __name__ == "__main__":
    sys.exit(main())