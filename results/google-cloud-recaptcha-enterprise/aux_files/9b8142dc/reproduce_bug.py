#!/usr/bin/env python3
"""Minimal reproduction of the path_template bug."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/google-cloud-recaptcha-enterprise_env/lib/python3.13/site-packages')

from google.api_core import path_template

# Minimal failing case
template = '/?'
args = []

print("Bug Report: path_template.validate returns False for its own expand output")
print("=" * 60)
print(f"Template: '{template}'")
print(f"Args: {args}")

expanded = path_template.expand(template, *args)
print(f"Expanded path: '{expanded}'")

is_valid = path_template.validate(template, expanded)
print(f"Validation result: {is_valid}")
print(f"Expected: True")

if not is_valid:
    print("\nBUG CONFIRMED: validate(template, expand(template)) should always return True")
    print("This violates the round-trip property of the path_template module.")
    
    # Let's understand why it fails
    print("\n--- Debugging ---")
    
    # Check the pattern generation
    import re
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
    
    def _replace_variable_with_pattern(match):
        """Replace a variable match with a pattern that can be used to validate it."""
        positional = match.group("positional")
        name = match.group("name")
        template = match.group("template")
        if name is not None:
            if not template:
                return r"([^/]+)"
            elif template == "**":
                return r"(.+)"
            else:
                # This would need recursive pattern generation
                return _generate_pattern_for_template(template)
        elif positional == "*":
            return r"([^/]+)"
        elif positional == "**":
            return r"(.+)"
        else:
            raise ValueError("Unknown template expression {}".format(match.group(0)))
    
    def _generate_pattern_for_template(tmpl):
        """Generate a pattern that can validate a path template."""
        return _VARIABLE_RE.sub(_replace_variable_with_pattern, tmpl)
    
    pattern = _generate_pattern_for_template(template) + "$"
    print(f"Generated validation pattern: {repr(pattern)}")
    
    match = re.match(pattern, expanded)
    print(f"Pattern matches expanded path: {match is not None}")
    
    # The issue is that '?' has special meaning in regex!
    print("\nRoot cause: '?' is a regex metacharacter (0 or 1 of preceding element)")
    print("The template '/??' generates pattern '/?$' which matches '/' but not '/?'")
    print("This is a bug in the validate function - it doesn't escape regex metacharacters")
    
# Test more cases with regex metacharacters
print("\n--- Testing other regex metacharacters ---")
metachar_templates = [
    '/?',     # Question mark (0 or 1)
    '/+',     # Plus (1 or more)
    '/.',     # Dot (any character)
    '/[',     # Opening bracket
    '/]',     # Closing bracket  
    '/$',     # Dollar (end of string)
    '/^',     # Caret (start of string)
    '/|',     # Pipe (alternation)
    '/(',     # Opening paren
    '/)',     # Closing paren
]

for tmpl in metachar_templates:
    try:
        expanded = path_template.expand(tmpl)
        is_valid = path_template.validate(tmpl, expanded)
        status = "PASS" if is_valid else "FAIL"
        print(f"{status}: template='{tmpl}', expanded='{expanded}', valid={is_valid}")
    except Exception as e:
        print(f"ERROR: template='{tmpl}', error={e}")