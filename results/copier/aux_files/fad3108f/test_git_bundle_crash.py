#!/usr/bin/env python3
"""Test is_git_bundle for crash bugs"""

import sys
from pathlib import Path
sys.path.insert(0, '/root/hypothesis-llm/envs/copier_env/lib/python3.13/site-packages')

import copier._vcs as vcs

# Test is_git_bundle with null character
print("Testing is_git_bundle with null character:")
try:
    result = vcs.is_git_bundle(Path('\x00'))
    print(f"Result: {result}")
except Exception as e:
    print(f"Exception: {type(e).__name__}: {e}")

# Test with other problematic paths
test_paths = [
    Path('\x00'),
    Path('test\x00'),
    Path('\x00test'),
    Path('te\x00st'),
]

for p in test_paths:
    try:
        result = vcs.is_git_bundle(p)
        print(f"is_git_bundle({repr(str(p))}) = {result}")
    except Exception as e:
        print(f"is_git_bundle({repr(str(p))}) raises {type(e).__name__}: {e}")