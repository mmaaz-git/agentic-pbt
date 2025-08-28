#!/usr/bin/env python3
"""Final minimal reproduction demonstrating the MockCommand argv[0] bug."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/testpath_env/lib/python3.13/site-packages')

import subprocess
from testpath import MockCommand

# Minimal reproduction
with MockCommand('testcmd') as mock:
    subprocess.run(['testcmd', 'arg1'], capture_output=True)
    calls = mock.get_calls()
    
    print("MockCommand argv[0] Bug Demonstration")
    print("="*40)
    print(f"Command invoked as: ['testcmd', 'arg1']")
    print(f"Recorded argv:      {calls[0]['argv']}")
    print(f"Expected argv:      ['testcmd', 'arg1']")
    print()
    print(f"Bug: argv[0] is '{calls[0]['argv'][0]}' instead of 'testcmd'")
    print()
    print("Real commands see just the name in argv[0] when called from PATH,")
    print("but MockCommand records the full path, violating mock fidelity.")