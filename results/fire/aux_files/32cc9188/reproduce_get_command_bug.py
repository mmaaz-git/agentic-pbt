#!/usr/bin/env python3
"""Minimal reproduction of GetCommand() bug with quotes."""

import fire.trace as trace

# Falsifying example from hypothesis
initial = None
args_list = [('', "0'0")]  # Second arg contains a single quote
targets = ['0']
filenames = ['0.py']
linenos = [1]

t = trace.FireTrace(initial)

# Add the component with the problematic args
args = args_list[0]
target = targets[0]
filename = filenames[0]
lineno = linenos[0]

t.AddCalledComponent(
    "result", target, args, filename, lineno, False,
    action=trace.CALLED_ROUTINE
)

# Get the command
command = t.GetCommand(include_separators=False)
print(f"Command: {command!r}")
print(f"Args: {args}")

# Check if the args are in the command
for part in args:
    if part:  # Skip empty strings
        if part in command:
            print(f"✓ Found '{part}' in command")
        else:
            print(f"✗ BUG: Expected '{part}' to be in command but it's not!")
            print(f"  The command is: {command!r}")
            print(f"  Looking for: {part!r}")