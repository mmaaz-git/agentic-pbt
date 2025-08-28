#!/usr/bin/env python3
"""Investigate the path_template expand/validate bug."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/google-cloud-recaptcha-enterprise_env/lib/python3.13/site-packages')

from google.api_core import path_template

# The failing case
template = '/？'
args = []

print(f"Template: {repr(template)}")
print(f"Args: {args}")

try:
    expanded = path_template.expand(template, *args)
    print(f"Expanded: {repr(expanded)}")
    
    result = path_template.validate(template, expanded)
    print(f"Validation result: {result}")
    print(f"Expected: True")
except Exception as e:
    print(f"Error during expand/validate: {e}")

# Let's test with simpler templates
print("\n--- Testing various simple templates ---")

test_cases = [
    ('/？', []),  # The failing case
    ('/?', []),   # ASCII question mark
    ('/', []),    # Just slash
    ('/test', []), # Normal path
    ('/test/*', ['value']), # With positional
    ('/test/{name}', {'name': 'value'}), # With named
]

for tmpl, args_or_kwargs in test_cases:
    print(f"\nTemplate: {repr(tmpl)}")
    try:
        if isinstance(args_or_kwargs, list):
            expanded = path_template.expand(tmpl, *args_or_kwargs)
            print(f"  Expanded with args {args_or_kwargs}: {repr(expanded)}")
        else:
            expanded = path_template.expand(tmpl, **args_or_kwargs)
            print(f"  Expanded with kwargs {args_or_kwargs}: {repr(expanded)}")
        
        result = path_template.validate(tmpl, expanded)
        print(f"  Validation: {result}")
    except Exception as e:
        print(f"  Error: {e}")

# Let's check if the issue is with the question mark
print("\n--- Checking the _VARIABLE_RE pattern ---")
import re

# From the source code
_VARIABLE_RE = re.compile(
    r"""
    (  # Capture the entire variable expression
        (?P<positional>\*\*?)  # Match & capture * and ** positional variables.
        |
        # Match & capture named variables {name}
        {
            (?P<name>[^/]+?)
            # Optionally match and capture the named variable's template.
            (?:=(?P<template>.+?))?
        }
    )
    """,
    re.VERBOSE,
)

test_strings = ['/？', '/?', '/*', '/{name}']
for s in test_strings:
    matches = list(_VARIABLE_RE.finditer(s))
    print(f"\nPattern matches in {repr(s)}: {len(matches)}")
    for m in matches:
        print(f"  Match: {m.group(0)}")
        print(f"    Positional: {m.group('positional')}")
        print(f"    Name: {m.group('name')}")

# Let's check if it's a Unicode issue
print("\n--- Unicode check ---")
print(f"Template contains non-ASCII: {'？' in template}")
print(f"Unicode codepoint of ？: {ord('？')}")  # Full-width question mark
print(f"Unicode codepoint of ?: {ord('?')}")   # ASCII question mark