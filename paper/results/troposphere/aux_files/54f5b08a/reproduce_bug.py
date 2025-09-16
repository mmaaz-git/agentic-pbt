#!/usr/bin/env python3

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.panorama as panorama

print("=== Bug Reproduction ===")
print("The issue: Properties with numeric names or names starting with digits")
print("are rejected even though they might be valid CloudFormation properties.")
print()

# Minimal reproduction
print("Attempting to create Package with property '0': 'value'")
try:
    pkg = panorama.Package("TestPkg", PackageName="test-package", **{"0": "value"})
    print("Success - package created")
except AttributeError as e:
    print(f"ERROR: {e}")
    print()
    print("This happens because __setattr__ in BaseAWSObject checks if the")
    print("property name is in self.propnames (the defined properties), and")
    print("if not, it raises an AttributeError.")
    print()
    print("The error message is misleading - it says the object doesn't")
    print("support the attribute, but the real issue is that numeric property")
    print("names or those starting with digits are always rejected.")

print()
print("The issue affects ALL troposphere classes derived from BaseAWSObject.")
print()

# Show that even valid-looking property names fail if they start with numbers
print("Even property names like '1abc' or '2Property' fail:")
for name in ["1abc", "2Property", "3_valid_name"]:
    try:
        pkg = panorama.Package("Test", PackageName="test", **{name: "value"})
        print(f"  {name}: Success")
    except AttributeError as e:
        print(f"  {name}: FAILED - {e}")

print()
print("This could be a problem if AWS CloudFormation ever uses properties")
print("with numeric names or names starting with digits.")