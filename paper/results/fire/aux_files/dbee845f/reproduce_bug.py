#!/usr/bin/env python3
"""Minimal reproduction of the dictionary key bug."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/fire_env/lib/python3.13/site-packages')

import fire.completion as completion

# Test case that reveals the bug
test_dict = {'foo_bar': None, 'baz_qux': 42, 'hello_world': 'test'}

print("Original dictionary keys:", list(test_dict.keys()))
completions = completion.Completions(test_dict)
print("Completions returned:", completions)

print("\nBug confirmed:")
for key in test_dict.keys():
    if key in completions:
        print(f"  ✓ '{key}' found in completions")
    else:
        print(f"  ✗ '{key}' NOT found in completions")
        transformed = key.replace('_', '-')
        if transformed in completions:
            print(f"    → But '{transformed}' IS in completions (underscore → hyphen transformation)")

# Let's also check VisibleMembers to understand where the transformation happens
print("\n\nInvestigating VisibleMembers:")
visible = completion.VisibleMembers(test_dict)
print("VisibleMembers returns:", visible)

# And check _FormatForCommand directly
print("\n\nTesting _FormatForCommand:")
for key in test_dict.keys():
    formatted = completion._FormatForCommand(key)
    print(f"  _FormatForCommand('{key}') = '{formatted}'")