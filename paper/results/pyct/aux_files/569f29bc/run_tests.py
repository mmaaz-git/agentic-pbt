#!/usr/bin/env python3
"""Run the hypothesis tests for pyct.report"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyct_env/lib/python3.13/site-packages')

import io
import subprocess
from unittest import mock
from hypothesis import given, strategies as st, assume, settings, example
from pyct.report import report

print("Testing pyct.report module with Hypothesis...")
print("=" * 60)

# Test 1: Basic crash test
print("\nTest 1: Testing with arbitrary package names...")
@given(st.text(min_size=1, max_size=10))
@example("; echo INJECTED")
@example("python && echo HACKED")
@example("$(whoami)")
@settings(max_examples=50)
def test_basic_functionality(package_name):
    assume('\x00' not in package_name)
    assume('\n' not in package_name)
    assume('\r' not in package_name)
    
    captured_output = io.StringIO()
    sys.stdout = captured_output
    try:
        report(package_name)
    finally:
        sys.stdout = sys.__stdout__
    
    output = captured_output.getvalue()
    assert package_name in output, f"Package name '{package_name}' not in output: {output}"
    assert '=' in output, f"No '=' in output: {output}"
    assert '#' in output, f"No '#' in output: {output}"

try:
    test_basic_functionality()
    print("✓ Basic functionality test passed")
except AssertionError as e:
    print(f"✗ Basic functionality test failed: {e}")
except Exception as e:
    print(f"✗ Test crashed: {e}")

# Test 2: Command injection
print("\nTest 2: Testing for command injection vulnerabilities...")
dangerous_inputs = [
    "; echo INJECTED",
    "&& echo INJECTED",
    "| echo INJECTED",
    "`echo INJECTED`",
    "$(echo INJECTED)",
    "python; touch /tmp/pwned",
    "python && cat /etc/passwd",
]

for inp in dangerous_inputs:
    captured_output = io.StringIO()
    sys.stdout = captured_output
    try:
        report(inp)
    finally:
        sys.stdout = sys.__stdout__
    
    output = captured_output.getvalue()
    if "INJECTED" in output:
        print(f"✗ COMMAND INJECTION FOUND with input: '{inp}'")
        print(f"  Output contained: {output}")
        break
else:
    print("✓ No command injection found in tested inputs")

# Test 3: Multiple packages
print("\nTest 3: Testing multiple packages...")
@given(st.lists(st.text(min_size=1, max_size=20), min_size=2, max_size=5))
@settings(max_examples=20)
def test_multiple_packages(package_names):
    for name in package_names:
        assume('\x00' not in name)
        assume('\n' not in name)
        assume('\r' not in name)
    
    captured_output = io.StringIO()
    sys.stdout = captured_output
    try:
        report(*package_names)
    finally:
        sys.stdout = sys.__stdout__
    
    output = captured_output.getvalue()
    lines = output.strip().split('\n')
    assert len(lines) == len(package_names), f"Expected {len(package_names)} lines, got {len(lines)}"

try:
    test_multiple_packages()
    print("✓ Multiple packages test passed")
except AssertionError as e:
    print(f"✗ Multiple packages test failed: {e}")
except Exception as e:
    print(f"✗ Test crashed: {e}")

# Test 4: Output format
print("\nTest 4: Testing output format consistency...")
@given(st.text(alphabet=st.characters(min_codepoint=32, max_codepoint=126), min_size=1, max_size=50))
@settings(max_examples=30)
def test_output_format(package_name):
    assume('\n' not in package_name)
    
    captured_output = io.StringIO()
    sys.stdout = captured_output
    try:
        report(package_name)
    finally:
        sys.stdout = sys.__stdout__
    
    output = captured_output.getvalue().strip()
    # Format should be: package=version{padding} # location
    equals_pos = output.find('=')
    hash_pos = output.find('#')
    
    assert equals_pos > 0, f"'=' not found properly in: {output}"
    assert hash_pos > equals_pos, f"'#' should come after '=' in: {output}"
    
    # The format string is "{0:30} # {1}" so check the padding
    first_part = output[:hash_pos].rstrip()
    # Due to padding, first part should aim for 30 chars
    if len(package_name) + len("=unknown") <= 30:
        assert len(first_part) <= 31, f"First part too long ({len(first_part)}): '{first_part}'"

try:
    test_output_format()
    print("✓ Output format test passed")
except AssertionError as e:
    print(f"✗ Output format test failed: {e}")
except Exception as e:
    print(f"✗ Test crashed: {e}")

# Test 5: System package special handling
print("\nTest 5: Testing 'system' package special handling...")
captured_output = io.StringIO()
sys.stdout = captured_output
try:
    report('system')
finally:
    sys.stdout = sys.__stdout__

output = captured_output.getvalue()
if 'system=' in output and 'OS:' in output:
    print("✓ 'system' package handled correctly")
else:
    print(f"✗ 'system' package not handled correctly: {output}")

print("\n" + "=" * 60)
print("Testing complete!")