#!/usr/bin/env python3
"""Minimal reproductions of bugs found in copier._vcs"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/copier_env/lib/python3.13/site-packages')

import copier._vcs as vcs
from packaging import version

print("=== Bug 1: get_repo crashes with null character ===")
try:
    result = vcs.get_repo('\x00')
    print(f"Result: {result}")
except Exception as e:
    print(f"CRASH: {type(e).__name__}: {e}")

print("\n=== Bug 2: valid_version accepts invalid version ===")
test_version = '1.0.0.0.0.0'
result = vcs.valid_version(test_version)
print(f"valid_version('{test_version}') = {result}")

# Verify with packaging
try:
    parsed = version.parse(test_version)
    print(f"packaging.version.parse('{test_version}') = {parsed}")
    print(f"Is this a valid PEP 440 version? {isinstance(parsed, version.Version)}")
except Exception as e:
    print(f"packaging.version.parse raised: {e}")

# Test more unusual versions
print("\n=== Testing more version strings ===")
test_versions = ['1.0.0.0.0.0', '1.2.3.4.5.6.7.8', 'v1.0.0', '1.0-beta']
for v in test_versions:
    vcs_result = vcs.valid_version(v)
    try:
        packaging_result = version.parse(v)
        packaging_valid = True
    except:
        packaging_valid = False
    print(f"  '{v}': vcs={vcs_result}, packaging={packaging_valid}")