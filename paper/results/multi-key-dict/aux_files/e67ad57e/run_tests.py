#!/usr/bin/env python3
import subprocess
import sys

result = subprocess.run([
    sys.executable, '-m', 'pytest', 
    'test_multi_key_dict_properties.py', 
    '-v', '--tb=short'
], capture_output=True, text=True)

print(result.stdout)
print(result.stderr)
sys.exit(result.returncode)