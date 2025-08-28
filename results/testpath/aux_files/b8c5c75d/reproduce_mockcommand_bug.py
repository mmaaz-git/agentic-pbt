#!/usr/bin/env python3
"""Minimal reproduction of MockCommand argv recording issue."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/testpath_env/lib/python3.13/site-packages')

import subprocess
from testpath import MockCommand

def test_mock_command_argv_recording():
    """Test what argv[0] is recorded when a mocked command is called."""
    
    cmd_name = 'mycommand'
    args = ['arg1', 'arg2']
    
    print(f"Testing MockCommand with command name: {cmd_name}")
    print(f"Arguments: {args}")
    
    with MockCommand(cmd_name) as mock_cmd:
        # Execute the command
        result = subprocess.run(
            [cmd_name] + args,
            capture_output=True,
            text=True,
            shell=False
        )
        
        # Get recorded calls
        calls = mock_cmd.get_calls()
        
        print(f"\nNumber of recorded calls: {len(calls)}")
        
        if calls:
            recorded_argv = calls[0]['argv']
            print(f"Recorded argv: {recorded_argv}")
            print(f"Expected argv: {[cmd_name] + args}")
            
            # Check if argv[0] is just the command name or full path
            if recorded_argv[0] != cmd_name:
                print(f"\nBUG FOUND: argv[0] is '{recorded_argv[0]}' instead of '{cmd_name}'")
                print("The recorded argv[0] contains the full path to the mock command,")
                print("not just the command name as would be expected.")
                return True
    
    return False

def test_with_assert_called():
    """Test MockCommand.assert_called() method to see expected behavior."""
    
    cmd_name = 'rsync'
    args = ['/var/log', 'backup-server:logs']
    
    print("\n\n=== Testing assert_called method ===")
    print(f"Command: {cmd_name}")
    print(f"Arguments: {args}")
    
    with MockCommand(cmd_name) as mock_cmd:
        # Execute the command
        subprocess.run([cmd_name] + args, capture_output=True)
        
        # According to the docstring, this should work:
        # mock_rsync.assert_called(['/var/log', 'backup-server:logs'])
        # Note: it expects args WITHOUT the command name
        
        try:
            mock_cmd.assert_called(args)
            print("assert_called(args) succeeded - this is the expected API")
        except AssertionError as e:
            print(f"assert_called(args) failed: {e}")
            
        # Let's check what was actually recorded
        calls = mock_cmd.get_calls()
        if calls:
            print(f"\nActual recorded argv: {calls[0]['argv']}")
            print(f"Actual recorded args (argv[1:]): {calls[0]['argv'][1:]}")

if __name__ == '__main__':
    bug_found = test_mock_command_argv_recording()
    test_with_assert_called()
    
    if bug_found:
        print("\n" + "="*60)
        print("CONCLUSION: This appears to be a genuine bug.")
        print("The argv[0] recorded includes the full path to the mock command,")
        print("which differs from standard Unix behavior where argv[0] is typically")
        print("the command name as invoked.")
        print("="*60)