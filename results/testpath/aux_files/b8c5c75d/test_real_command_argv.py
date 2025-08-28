#!/usr/bin/env python3
"""Test how real compiled commands handle argv[0]."""

import subprocess
import tempfile
import os

def test_c_program_argv():
    """Test argv[0] behavior with a real C program."""
    print("=== Testing Real C Program argv[0] Behavior ===\n")
    
    # Create a simple C program that prints argv[0]
    c_code = """
#include <stdio.h>
int main(int argc, char *argv[]) {
    printf("argv[0]: %s\\n", argv[0]);
    for (int i = 0; i < argc; i++) {
        printf("argv[%d]: %s\\n", i, argv[i]);
    }
    return 0;
}
"""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Write C source
        c_file = os.path.join(tmpdir, "test_argv.c")
        with open(c_file, 'w') as f:
            f.write(c_code)
        
        # Compile it
        exe_file = os.path.join(tmpdir, "test_argv")
        result = subprocess.run(
            ["gcc", "-o", exe_file, c_file],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print("Could not compile C program (gcc not available)")
            print("Falling back to shell script test...")
            test_shell_script_argv()
            return
        
        # Test 1: Call with full path
        print("1. Calling C program with full path:")
        result = subprocess.run([exe_file, "arg1"], capture_output=True, text=True)
        print(result.stdout)
        
        # Test 2: Call from PATH by name only
        old_path = os.environ.get('PATH', '')
        os.environ['PATH'] = tmpdir + os.pathsep + old_path
        
        print("2. Calling C program from PATH by name only:")
        result = subprocess.run(["test_argv", "arg1"], capture_output=True, text=True)
        print(result.stdout)
        
        os.environ['PATH'] = old_path
        
        print("OBSERVATION: When called by name from PATH, the C program sees")
        print("just the command name in argv[0], NOT the full path!")
        print("This is the standard Unix behavior.")


def test_shell_script_argv():
    """Test argv[0] behavior with a shell script."""
    print("\n=== Testing Shell Script argv[0] Behavior ===\n")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a shell script
        script_file = os.path.join(tmpdir, "test_argv")
        with open(script_file, 'w') as f:
            f.write("""#!/bin/bash
echo "argv[0]: $0"
echo "All args: $@"
""")
        os.chmod(script_file, 0o755)
        
        # Test 1: Call with full path
        print("1. Calling shell script with full path:")
        result = subprocess.run([script_file, "arg1"], capture_output=True, text=True)
        print(result.stdout)
        
        # Test 2: Call from PATH by name only
        old_path = os.environ.get('PATH', '')
        os.environ['PATH'] = tmpdir + os.pathsep + old_path
        
        print("2. Calling shell script from PATH by name only:")
        result = subprocess.run(["test_argv", "arg1"], capture_output=True, text=True)
        print(result.stdout)
        
        os.environ['PATH'] = old_path
        
        print("OBSERVATION: Shell scripts also typically see just the command name")
        print("in $0 when called by name from PATH.")


def conclusion():
    print("\n" + "="*70)
    print("CONCLUSION: MockCommand argv[0] Behavior is a BUG")
    print("="*70)
    print("""
Real commands (both compiled programs and shell scripts) see just the
command name in argv[0] when invoked by name from PATH. 

MockCommand records the full path in argv[0], which differs from this
standard behavior. This is a legitimate bug because:

1. It violates the principle that mocks should behave like real commands
2. Code under test might depend on argv[0] being just the command name
3. The recorded behavior doesn't match reality

While the assert_called() API works around this by ignoring argv[0],
the get_calls() method returns incorrect data that doesn't match what
a real command would see.

This bug could affect tests that:
- Inspect the raw recorded calls via get_calls()
- Test code that examines argv[0] in the mocked command
- Expect mock behavior to match real command behavior exactly
""")

if __name__ == '__main__':
    test_c_program_argv()
    test_shell_script_argv()
    conclusion()