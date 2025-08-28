#!/usr/bin/env python3
"""Simple test runner that uses subprocess to run tests"""

import subprocess
import sys

# Run the test using the venv python
result = subprocess.run(
    ['/root/hypothesis-llm/envs/datadog-checks-base_env/bin/python3', 'test_datadog_checks_properties.py'],
    capture_output=True,
    text=True
)

print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr, file=sys.stderr)

sys.exit(result.returncode)