#!/usr/bin/env python3

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.kendra as kendra
from troposphere.validators import integer, boolean, double

# Check specific classes that we know have integer/boolean properties
print("=== Checking specific properties ===")

# CapacityUnitsConfiguration has integer properties
print("\nCapacityUnitsConfiguration.props:")
for prop_name, prop_def in kendra.CapacityUnitsConfiguration.props.items():
    prop_type, required = prop_def
    print(f"  {prop_name}: {prop_type}, required={required}")
    # Test if it's the integer validator
    if prop_type == integer:
        print(f"    -> This is the integer validator!")

# DocumentAttributeTarget has boolean property
print("\nDocumentAttributeTarget.props:")
for prop_name, prop_def in kendra.DocumentAttributeTarget.props.items():
    prop_type, required = prop_def
    print(f"  {prop_name}: {prop_type}, required={required}")
    if prop_type == boolean:
        print(f"    -> This is the boolean validator!")

# ConnectionConfiguration has integer property (DatabasePort)
print("\nConnectionConfiguration.props:")
for prop_name, prop_def in kendra.ConnectionConfiguration.props.items():
    prop_type, required = prop_def
    print(f"  {prop_name}: {prop_type}, required={required}")
    if prop_type == integer:
        print(f"    -> This is the integer validator!")

# Test the validators themselves
print("\n=== Testing validators ===")
print(f"integer validator: {integer}")
print(f"boolean validator: {boolean}") 
print(f"double validator: {double}")

# Try calling them
print("\nTesting integer validator:")
print(f"  integer(5) = {integer(5)}")
print(f"  integer('5') = {integer('5')}")
try:
    print(f"  integer('not_a_number') = {integer('not_a_number')}")
except Exception as e:
    print(f"  integer('not_a_number') raised: {e}")

print("\nTesting boolean validator:")
print(f"  boolean(True) = {boolean(True)}")
print(f"  boolean('true') = {boolean('true')}")
try:
    print(f"  boolean('not_bool') = {boolean('not_bool')}")
except Exception as e:
    print(f"  boolean('not_bool') raised: {e}")