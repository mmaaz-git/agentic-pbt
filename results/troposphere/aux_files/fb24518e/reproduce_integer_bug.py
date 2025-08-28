#!/usr/bin/env python3
"""
Minimal reproduction of integer validator bug in troposphere.
The integer validator doesn't convert float values to integers.
"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.greengrass as greengrass

# Create a Logger with integer Space property
logger = greengrass.Logger(
    "TestLogger",
    Component="test",
    Id="logger-id",
    Level="INFO",
    Type="FileSystem"
)

# Set Space to a float value
logger.Space = 42.0

# Get the dict representation
result = logger.to_dict()

print(f"Input value: 42.0 (type: {type(42.0).__name__})")
print(f"Output value: {result.get('Space')} (type: {type(result.get('Space')).__name__})")
print(f"Expected: integer type, Got: {type(result.get('Space')).__name__}")

# This shows the bug: the integer validator accepts floats but doesn't convert them
assert isinstance(result.get('Space'), int), f"Space should be int, but is {type(result.get('Space')).__name__}"