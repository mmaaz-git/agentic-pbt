"""Test if MockCommand works correctly in binary mode"""

import subprocess
import testpath.commands as commands

# Test with binary mode capture
with commands.MockCommand.fixed_output('test_binary', stdout='\r', stderr='x\ry', exit_status=0):
    # Try capturing in binary mode
    result = subprocess.run(['test_binary'], capture_output=True)
    
    print(f"Binary mode stdout: {repr(result.stdout)}")
    print(f"Binary mode stderr: {repr(result.stderr)}")
    
    # Check if we get the expected bytes
    expected_stdout = b'\r'
    expected_stderr = b'x\ry'
    
    if result.stdout == expected_stdout:
        print("Binary stdout matches!")
    else:
        print(f"Binary stdout mismatch: expected {repr(expected_stdout)}, got {repr(result.stdout)}")
    
    if result.stderr == expected_stderr:
        print("Binary stderr matches!")
    else:
        print(f"Binary stderr mismatch: expected {repr(expected_stderr)}, got {repr(result.stderr)}")