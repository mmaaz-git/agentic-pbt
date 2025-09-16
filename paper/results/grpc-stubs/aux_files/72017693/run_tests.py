#!/usr/bin/env python3
import subprocess
import sys

result = subprocess.run([
    '/root/hypothesis-llm/envs/grpc-stubs_env/bin/python3', 
    '-m', 'pytest', 
    'test_grpc_status_properties.py', 
    '-v', '--tb=short'
], capture_output=True, text=True)

print(result.stdout)
print(result.stderr)
sys.exit(result.returncode)