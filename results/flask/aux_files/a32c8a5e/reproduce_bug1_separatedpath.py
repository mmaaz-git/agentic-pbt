"""Reproduce SeparatedPathType empty string handling bug"""

import os
import flask.cli

# Test the round-trip property
paths = []
joined = os.pathsep.join(paths)  # Results in empty string ""
print(f"Original paths: {paths}")
print(f"Joined string: {joined!r}")

sep_type = flask.cli.SeparatedPathType()
split_result = sep_type.split_envvar_value(joined)
print(f"Split result: {list(split_result)}")

# Check if round-trip works
if list(split_result) == paths:
    print("✓ Round-trip successful")
else:
    print("✗ Round-trip FAILED")
    print(f"  Expected: {paths}")
    print(f"  Got: {list(split_result)}")
    
# This is a bug because:
# 1. It violates the round-trip property
# 2. An empty environment variable should represent "no paths", not "one empty path"