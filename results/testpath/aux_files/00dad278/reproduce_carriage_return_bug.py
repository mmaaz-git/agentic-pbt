"""Minimal reproducer for carriage return bug in MockCommand.fixed_output"""

import subprocess
import sys
import testpath.commands as commands

# Test case 1: stdout with carriage return
with commands.MockCommand.fixed_output('test_cmd', stdout='\r', stderr='', exit_status=0):
    result = subprocess.run(['test_cmd'], capture_output=True, text=True)
    if result.stdout == '\r':
        print("Test 1 passed: stdout with \\r preserved correctly")
    else:
        print(f"Test 1 FAILED: Expected stdout='\\r', got stdout={repr(result.stdout)}")

# Test case 2: stderr with carriage return  
with commands.MockCommand.fixed_output('test_cmd2', stdout='', stderr='\r', exit_status=0):
    result = subprocess.run(['test_cmd2'], capture_output=True, text=True)
    if result.stderr == '\r':
        print("Test 2 passed: stderr with \\r preserved correctly")
    else:
        print(f"Test 2 FAILED: Expected stderr='\\r', got stderr={repr(result.stderr)}")

# Test case 3: mixed carriage returns and newlines
with commands.MockCommand.fixed_output('test_cmd3', stdout='a\rb\nc\r\n', stderr='', exit_status=0):
    result = subprocess.run(['test_cmd3'], capture_output=True, text=True)
    if result.stdout == 'a\rb\nc\r\n':
        print("Test 3 passed: mixed \\r and \\n preserved correctly")
    else:
        print(f"Test 3 FAILED: Expected stdout='a\\rb\\nc\\r\\n', got stdout={repr(result.stdout)}")