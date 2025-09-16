#!/usr/bin/env python3
import sys
import subprocess

result = subprocess.run([
    '/root/hypothesis-llm/envs/troposphere_env/bin/python', 
    '-m', 'pytest', 
    'test_troposphere_budgets.py', 
    '-v'
], capture_output=True, text=True)

print(result.stdout)
print(result.stderr)
sys.exit(result.returncode)