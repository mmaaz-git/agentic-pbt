#!/usr/bin/env python3
"""Run the property-based tests."""

import sys
import subprocess

# Run pytest with the test file
result = subprocess.run(
    ['/root/hypothesis-llm/envs/troposphere_env/bin/pytest', 
     'test_troposphere_licensemanager.py', '-v'],
    capture_output=True,
    text=True
)

print(result.stdout)
print(result.stderr)
sys.exit(result.returncode)