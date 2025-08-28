#!/usr/bin/env python3
import subprocess
import sys

# Run pytest with the venv python
result = subprocess.run(
    ["./venv/bin/python", "-m", "pytest", "test_troposphere_properties.py", "-v", "--tb=short"],
    capture_output=True,
    text=True
)

print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr)

sys.exit(result.returncode)