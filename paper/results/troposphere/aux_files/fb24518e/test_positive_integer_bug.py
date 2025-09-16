#!/usr/bin/env python3
"""
Test if positive_integer validator has the same bug as integer validator.
"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.greengrass as greengrass

# FunctionConfiguration has MemorySize property with positive_integer validator
func_config = greengrass.FunctionConfiguration("TestConfig")

# Set MemorySize to a float value
func_config.MemorySize = 128.0

# Get the dict representation
result = func_config.to_dict()

print(f"Input value: 128.0 (type: {type(128.0).__name__})")
print(f"Output value: {result.get('MemorySize')} (type: {type(result.get('MemorySize')).__name__})")

# Check if positive_integer has the same issue
if 'MemorySize' in result:
    assert isinstance(result['MemorySize'], int), f"MemorySize should be int, but is {type(result['MemorySize']).__name__}"