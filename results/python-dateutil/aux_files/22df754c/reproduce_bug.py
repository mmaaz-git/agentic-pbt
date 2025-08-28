#!/usr/bin/env python3
"""Reproduce the control character bug in lxml.isoschematron.stylesheet_params"""

import lxml.isoschematron as iso

# Demonstrate the bug
control_char_string = "\x1f"  # Unit separator control character

try:
    result = iso.stylesheet_params(my_param=control_char_string)
    print("Unexpectedly succeeded")
except ValueError as e:
    print(f"Bug reproduced: stylesheet_params crashes with: {e}")
    print(f"Input was a valid Python string: {repr(control_char_string)}")
    print("\nThis is a bug because:")
    print("1. The function accepts string parameters")
    print("2. Control characters are valid in Python strings")
    print("3. The documentation doesn't mention this limitation")
    print("4. The error message doesn't clearly indicate the issue is in the user's input")