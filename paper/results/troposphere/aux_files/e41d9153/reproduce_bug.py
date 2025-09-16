#!/usr/bin/env python3
"""Minimal reproduction of the empty title bug in troposphere."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere
from troposphere import Parameter, Template

print(f"Troposphere version: {troposphere.__version__}")
print("\nReproducing empty title bug...")
print("-" * 40)

# The bug: Empty string passes title validation
param = Parameter("", Type="String", Default="test")
print(f"Created Parameter with empty title: '{param.title}'")

# This should fail validation according to the code at line 327-328:
# if not self.title or not valid_names.match(self.title):
#     raise ValueError('Name "%s" not alphanumeric' % self.title)

# Let's check what happens when we add it to a template
template = Template()
template.add_parameter(param)

# Check the template JSON output
json_output = template.to_json()
print(f"\nTemplate JSON output:")
print(json_output)

# Check if CloudFormation would accept this
print("\nAnalysis:")
print("1. The Parameter class has a validate_title() method that should reject empty titles")
print("2. The validation checks: 'if not self.title or not valid_names.match(self.title)'")
print("3. An empty string should fail the 'if not self.title' check")
print("4. But the parameter is created successfully with an empty title")
print("\nThis is a bug because CloudFormation requires non-empty logical names for parameters.")