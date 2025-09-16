#!/usr/bin/env python3
"""Test for validation message printing bug."""

import sys
import io
from contextlib import redirect_stderr, redirect_stdout

sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.mediastore import MetricPolicy

print("Testing validation message bug...")
print("=" * 60)

# Capture stdout and stderr
captured_output = io.StringIO()
captured_error = io.StringIO()

print("\n1. Creating MetricPolicy with invalid status (capturing output)...")

with redirect_stdout(captured_output), redirect_stderr(captured_error):
    try:
        # This prints an error message even though it raises ValueError
        policy = MetricPolicy(ContainerLevelMetrics="INVALID_STATUS")
        print("Policy created (shouldn't happen)")
    except ValueError as e:
        pass  # Expected

# Check what was printed
stdout_content = captured_output.getvalue()
stderr_content = captured_error.getvalue()

if stdout_content:
    print(f"   STDOUT captured: {repr(stdout_content)}")
if stderr_content:
    print(f"   STDERR captured: {repr(stderr_content)}")

if not stdout_content and not stderr_content:
    print("   ✓ No output captured (clean error handling)")
else:
    print("   ✗ BUG: Error message printed to stdout/stderr before raising exception")

# Test with valid value
print("\n2. Creating MetricPolicy with valid status...")
captured_output2 = io.StringIO()
captured_error2 = io.StringIO()

with redirect_stdout(captured_output2), redirect_stderr(captured_error2):
    try:
        policy = MetricPolicy(ContainerLevelMetrics="ENABLED")
        print("   ✓ Policy created successfully")
    except ValueError as e:
        print(f"   ✗ Unexpected error: {e}")

# Let's trace where the message comes from
print("\n3. Investigating the validation flow...")
print("   Looking at the error message pattern...")

# Test multiple invalid values to see the pattern
test_values = ["", "enabled", "ENABLE", "YES", "1", 123, None]

for value in test_values:
    print(f"\n   Testing value: {repr(value)}")
    captured = io.StringIO()
    with redirect_stderr(captured):
        try:
            policy = MetricPolicy(ContainerLevelMetrics=value)
        except (ValueError, TypeError) as e:
            error_msg = str(e)
            stderr_msg = captured.getvalue()
            if stderr_msg:
                print(f"      STDERR: {repr(stderr_msg)}")
            print(f"      Exception: {error_msg}")