#!/usr/bin/env python3
import sys
import subprocess

# Run the tests
result = subprocess.run([
    '/root/hypothesis-llm/envs/dagster-postgres_env/bin/python', 
    '-m', 'pytest', 
    'test_dagster_postgres_properties.py', 
    '-v', 
    '--tb=short'
], capture_output=True, text=True)

print(result.stdout)
print(result.stderr)
sys.exit(result.returncode)