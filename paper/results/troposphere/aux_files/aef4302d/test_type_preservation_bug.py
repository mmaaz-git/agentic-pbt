#!/usr/bin/env python3

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.kendra as kendra
from troposphere import Template, Output
import json

print("=== Testing Type Preservation Bug ===\n")

# Create configurations with different input types
configs = [
    ("Integer input", kendra.CapacityUnitsConfiguration(
        QueryCapacityUnits=10,
        StorageCapacityUnits=20
    )),
    ("String number input", kendra.CapacityUnitsConfiguration(
        QueryCapacityUnits="10",
        StorageCapacityUnits="20"
    )),
    ("String with leading zeros", kendra.CapacityUnitsConfiguration(
        QueryCapacityUnits="010",
        StorageCapacityUnits="020"
    )),
    ("Mixed types", kendra.CapacityUnitsConfiguration(
        QueryCapacityUnits=10,
        StorageCapacityUnits="20"
    ))
]

print("Comparing to_dict() outputs:")
for name, config in configs:
    result = config.to_dict()
    print(f"\n{name}:")
    print(f"  QueryCapacityUnits: {repr(result['QueryCapacityUnits'])} (type: {type(result['QueryCapacityUnits']).__name__})")
    print(f"  StorageCapacityUnits: {repr(result['StorageCapacityUnits'])} (type: {type(result['StorageCapacityUnits']).__name__})")
    
    # JSON serialization
    json_str = json.dumps(result)
    print(f"  JSON: {json_str}")

print("\n=== CloudFormation Template Generation ===")

# Create a template with these resources
template = Template()

# Add an Index that uses CapacityUnitsConfiguration
index = kendra.Index(
    "MyKendraIndex",
    Name="TestIndex",
    Edition="DEVELOPER_EDITION",
    RoleArn="arn:aws:iam::123456789012:role/KendraRole",
    CapacityUnits=kendra.CapacityUnitsConfiguration(
        QueryCapacityUnits="10",  # String input
        StorageCapacityUnits=10    # Integer input
    )
)
template.add_resource(index)

# Generate the CloudFormation JSON
cf_json = template.to_json()
cf_dict = json.loads(cf_json)

print("CloudFormation template fragment:")
capacity_units = cf_dict['Resources']['MyKendraIndex']['Properties']['CapacityUnits']
print(json.dumps(capacity_units, indent=2))

print("\n=== The Problem ===")
print("1. The integer validator accepts string numbers but doesn't convert them")
print("2. This results in mixed types in the CloudFormation template")
print("3. CloudFormation expects integer values, not strings")
print("4. String values like '010' preserve leading zeros, which changes the value")
print("5. This type inconsistency can cause deployment failures")

print("\n=== Demonstrating the issue with arithmetic ===")

# If CloudFormation or downstream services try to do arithmetic...
query_units_int = 10
query_units_str = "10"
query_units_zeros = "010"

print(f"Integer 10 * 2 = {query_units_int * 2}")
print(f"String '10' * 2 = {query_units_str * 2}")  # String repetition!
print(f"String '010' as int = {int(query_units_zeros)}")  # Loses leading zero

print("\nThis type preservation behavior violates the principle of")
print("'parse, don't validate' - the validator should either reject")
print("strings or convert them to integers, not pass them through.")