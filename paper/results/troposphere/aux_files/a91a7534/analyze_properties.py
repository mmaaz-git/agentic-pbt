#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import inspect
import troposphere
from troposphere import Template, Tags, Parameter, Output, Ref, Join, Base64

# Test that I can import and use basic features
t = Template()
print("Template created successfully")

# Check some interesting functions that might have properties to test
print("\n=== Analyzing potential properties ===")

# 1. Tags - they seem to have interesting behavior with add operator
print("\n1. Tags class:")
print("   - Has __add__ method for concatenation")
print("   - Has from_dict and to_dict methods")
tags1 = Tags(foo="bar")
tags2 = Tags(baz="qux")
combined = tags1 + tags2
print(f"   - Tags addition works: {combined.to_dict()}")

# 2. Template limits
print("\n2. Template limits (constants):")
print(f"   - MAX_MAPPINGS: {troposphere.MAX_MAPPINGS}")
print(f"   - MAX_OUTPUTS: {troposphere.MAX_OUTPUTS}")
print(f"   - MAX_PARAMETERS: {troposphere.MAX_PARAMETERS}")
print(f"   - MAX_RESOURCES: {troposphere.MAX_RESOURCES}")
print(f"   - PARAMETER_TITLE_MAX: {troposphere.PARAMETER_TITLE_MAX}")

# 3. encode_to_dict function
print("\n3. encode_to_dict function:")
print("   - Should handle dicts, lists, and objects with to_dict")
print("   - Recursively encodes nested structures")

# 4. Join helper function  
print("\n4. Join function:")
print("   - Has delimiter validation")
print("   - Signature:", inspect.signature(troposphere.Join))

# 5. Parameter validation
print("\n5. Parameter class:")
print("   - Has title length validation (max 255)")
print("   - Has type validation for Default values")
print("   - Different validation rules for String/Number/List types")

# 6. valid_names regex
print("\n6. valid_names pattern:")
print(f"   - Pattern: {troposphere.valid_names.pattern}")
print("   - Used for validating resource names (alphanumeric only)")

# 7. depends_on_helper
print("\n7. depends_on_helper function:")
print("   - Handles AWSObject instances by extracting .title")
print("   - Handles lists recursively")
print("   - Signature:", inspect.signature(troposphere.depends_on_helper))