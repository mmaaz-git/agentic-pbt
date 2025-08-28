"""Minimal reproduction of the flag detection bug in fire.core."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/fire_env/lib/python3.13/site-packages')

import fire.core as core

# Demonstrate the bug
test_inputs = ['0', '-1', 'abc', '---', '']

print("Flag detection functions return None instead of False:\n")
for input_str in test_inputs:
    result = core._IsFlag(input_str)
    print(f"  _IsFlag('{input_str}') = {repr(result)}")
    assert result in (True, False), f"Expected boolean, got {type(result).__name__}"