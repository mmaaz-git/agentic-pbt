#!/usr/bin/env /root/hypothesis-llm/envs/troposphere_env/bin/python3
"""
Explore troposphere module to identify testable properties
"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere
import inspect
from troposphere import Template, Parameter, Output, Ref, Tags, AWSObject, BaseAWSObject
from troposphere import validators

print("=== Troposphere Module Overview ===")
print(f"Version: {troposphere.__version__}")
print()

# Explore key classes and their docstrings
print("=== Key Classes ===")
for cls_name in ['Template', 'Parameter', 'Output', 'AWSObject', 'BaseAWSObject', 'Tags', 'Ref']:
    cls = getattr(troposphere, cls_name)
    print(f"\n{cls_name}:")
    if cls.__doc__:
        print(f"  Doc: {cls.__doc__[:200]}")
    
    # Show key methods
    methods = [m for m in dir(cls) if not m.startswith('_') and callable(getattr(cls, m))]
    print(f"  Key methods: {', '.join(methods[:10])}")

# Look at validators
print("\n=== Validators ===")
validator_funcs = [name for name in dir(validators) if not name.startswith('_')]
print(f"Available validators: {', '.join(validator_funcs[:15])}")

# Check constants
print("\n=== Template Limits (from code) ===")
print(f"MAX_MAPPINGS: {troposphere.MAX_MAPPINGS}")
print(f"MAX_OUTPUTS: {troposphere.MAX_OUTPUTS}")
print(f"MAX_PARAMETERS: {troposphere.MAX_PARAMETERS}")
print(f"MAX_RESOURCES: {troposphere.MAX_RESOURCES}")
print(f"PARAMETER_TITLE_MAX: {troposphere.PARAMETER_TITLE_MAX}")

# Check title validation regex
print("\n=== Title Validation ===")
print(f"Valid names regex pattern: {troposphere.valid_names.pattern}")

# Test some basic functionality
print("\n=== Basic Functionality Test ===")
try:
    t = Template()
    p = Parameter("TestParam", Type="String", Default="test")
    t.add_parameter(p)
    print(f"Created template with parameter: {p.title}")
    print(f"Parameter properties: {p.properties}")
except Exception as e:
    print(f"Error creating basic objects: {e}")

# Check Tags behavior
print("\n=== Tags Behavior ===")
try:
    tags1 = Tags(Key1="Value1", Key2="Value2")
    tags2 = Tags(Key3="Value3")
    combined = tags1 + tags2
    print(f"Tags1: {tags1.to_dict()}")
    print(f"Tags2: {tags2.to_dict()}")
    print(f"Combined: {combined.to_dict()}")
except Exception as e:
    print(f"Error with Tags: {e}")

# Check Ref behavior
print("\n=== Ref Behavior ===")
try:
    ref1 = Ref("MyResource")
    ref2 = Ref("MyResource")
    ref3 = Ref("OtherResource")
    print(f"ref1 == ref2: {ref1 == ref2}")
    print(f"ref1 == ref3: {ref1 == ref3}")
    print(f"ref1.data: {ref1.data}")
except Exception as e:
    print(f"Error with Ref: {e}")