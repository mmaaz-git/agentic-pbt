#!/usr/bin/env python3
"""Test for missing docstring in IoTJobRateIncreaseCriteria."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.greengrassv2 as ggv2

# Check for consistent docstrings
classes_to_check = [
    ("ComponentDependencyRequirement", True),  # Has docstring
    ("ComponentPlatform", True),  # Has docstring
    ("LambdaEventSource", True),  # Has docstring
    ("IoTJobRateIncreaseCriteria", False),  # Missing docstring!
    ("IoTJobExponentialRolloutRate", True),  # Has docstring
]

print("Checking for docstring consistency...")
print("=" * 60)

for class_name, should_have_docstring in classes_to_check:
    cls = getattr(ggv2, class_name)
    has_docstring = cls.__doc__ is not None and "http://docs.aws.amazon.com" in (cls.__doc__ or "")
    
    if should_have_docstring:
        if has_docstring:
            print(f"✓ {class_name}: Has AWS documentation link")
        else:
            print(f"✗ {class_name}: MISSING AWS documentation link")
    else:
        if has_docstring:
            print(f"✗ {class_name}: Unexpectedly has documentation")
        else:
            print(f"✓ {class_name}: Correctly missing documentation (internal class?)")

print("\n" + "=" * 60)
print("Analysis complete!")
print("\nPotential issue found:")
print("IoTJobRateIncreaseCriteria is missing its AWS CloudFormation documentation link.")
print("This could be:")
print("1. An oversight (missing documentation)")
print("2. An internal/undocumented AWS property")
print("3. A property that doesn't have official AWS docs yet")