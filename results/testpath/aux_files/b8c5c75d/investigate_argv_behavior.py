#!/usr/bin/env python3
"""Investigate whether the full path in argv[0] is intentional or a bug."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/testpath_env/lib/python3.13/site-packages')

import subprocess
import os
from testpath import MockCommand

def check_real_command_behavior():
    """Check how real commands report argv[0]."""
    print("=== Real Command Behavior ===")
    
    # Create a simple Python script that prints its argv
    script_content = """#!/usr/bin/env python3
import sys
print("argv[0]:", sys.argv[0])
print("Full argv:", sys.argv)
"""
    
    # Write to a temp file  
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(script_content)
        script_path = f.name
    
    os.chmod(script_path, 0o755)
    
    # Test 1: Call with full path
    print("\n1. Calling with full path:")
    result = subprocess.run([script_path, 'arg1'], capture_output=True, text=True)
    print(result.stdout)
    
    # Test 2: Call from PATH
    script_dir = os.path.dirname(script_path)
    script_name = os.path.basename(script_path)
    
    # Add to PATH and call by name
    old_path = os.environ.get('PATH', '')
    os.environ['PATH'] = script_dir + os.pathsep + old_path
    
    print("2. Calling from PATH by name:")
    result = subprocess.run([script_name, 'arg1'], capture_output=True, text=True)
    print(result.stdout)
    
    # Restore PATH
    os.environ['PATH'] = old_path
    os.unlink(script_path)
    
    print("\nOBSERVATION: Real commands show different argv[0] depending on how they're called.")
    print("When called by name from PATH, argv[0] is typically just the name.")


def check_mockcommand_internal_behavior():
    """Check how MockCommand's internal script records argv."""
    print("\n\n=== MockCommand Internal Behavior ===")
    
    # Look at what MockCommand actually does
    print("MockCommand creates a script that records sys.argv directly.")
    print("In Python, sys.argv[0] is the script name as invoked.")
    print("")
    print("When subprocess.run(['mycommand']) is called:")
    print("1. subprocess searches PATH for 'mycommand'")
    print("2. It finds /tmp/xxx/mycommand")  
    print("3. It executes that file")
    print("4. Python sets sys.argv[0] to the actual path used")
    print("")
    print("This means the full path in argv[0] is a side effect of how")
    print("subprocess and Python handle command execution.")


def test_impact_on_assert_called():
    """Test if this impacts the assert_called() functionality."""
    print("\n\n=== Impact on assert_called() ===")
    
    with MockCommand('testcmd') as mock:
        subprocess.run(['testcmd', 'arg1', 'arg2'], capture_output=True)
        
        # The API design of assert_called expects args WITHOUT command name
        # This works correctly:
        mock.assert_called(['arg1', 'arg2'])
        print("✓ assert_called(['arg1', 'arg2']) works as documented")
        
        # This would fail because it includes the command name:
        try:
            mock.assert_called(['testcmd', 'arg1', 'arg2'])
            print("✗ assert_called(['testcmd', 'arg1', 'arg2']) incorrectly succeeded")
        except AssertionError:
            print("✓ assert_called(['testcmd', 'arg1', 'arg2']) correctly fails")
    
    print("\nThe assert_called() API expects args without the command name,")
    print("which aligns with the current recording behavior (using argv[1:]).")


def final_analysis():
    """Determine if this is a bug or expected behavior."""
    print("\n\n" + "="*70)
    print("FINAL ANALYSIS")
    print("="*70)
    
    print("""
The recorded argv[0] containing the full path appears to be expected behavior
due to how Python and subprocess interact:

1. subprocess.run(['cmd']) searches PATH and finds /tmp/xxx/cmd
2. Python is invoked with the full path as argv[0]
3. The recording script captures sys.argv as-is

However, this creates a DISCREPANCY with typical Unix command behavior:
- Real commands invoked by name typically see just the name in argv[0]
- MockCommand records the full path instead

This could be considered a bug because:
- It violates the principle that mocks should behave like the real thing
- Code under test might depend on argv[0] being just the command name
- The recorded calls don't match what a real command would see

The assert_called() API works around this by comparing only argv[1:],
but get_calls() returns the full argv with the unexpected path.
""")

if __name__ == '__main__':
    check_real_command_behavior()
    check_mockcommand_internal_behavior()
    test_impact_on_assert_called()
    final_analysis()