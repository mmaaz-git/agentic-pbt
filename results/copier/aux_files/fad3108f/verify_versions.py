#!/usr/bin/env python3
"""Verify version behavior"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/copier_env/lib/python3.13/site-packages')

from packaging import version
from packaging.version import Version

# Check what type of version objects we get
test_versions = ['1.0.0.0.0.0', 'v1.0.0', '1.0-beta']

for v_str in test_versions:
    parsed = version.parse(v_str)
    print(f"version.parse('{v_str}'):")
    print(f"  Result: {parsed}")
    print(f"  Type: {type(parsed)}")
    print(f"  Is Version: {isinstance(parsed, Version)}")
    print()