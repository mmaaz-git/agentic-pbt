#!/usr/bin/env python3
import sys
import subprocess

# Run pytest on the test file
result = subprocess.run(
    ['/root/hypothesis-llm/envs/trino_env/bin/pytest', 
     'test_trino_auth_properties.py', 
     '-v', 
     '--tb=short'],
    capture_output=True,
    text=True
)

print(result.stdout)
print(result.stderr)
sys.exit(result.returncode)