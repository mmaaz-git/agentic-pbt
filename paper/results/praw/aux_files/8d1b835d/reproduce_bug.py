#!/usr/bin/env python3
"""Minimal reproduction of the camel_to_snake bug in PRAW."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/praw_env/lib/python3.13/site-packages')

from praw.util import camel_to_snake

# Bug: camel_to_snake incorrectly handles 3+ consecutive uppercase letters
# followed by a lowercase letter

print("Bug reproduction: camel_to_snake with 'APIv2' pattern\n")

# These cases demonstrate the bug
test_cases = [
    ("APIv2", "apiv2", "ap_iv2"),  # (input, expected, actual)
    ("APIv1", "apiv1", "ap_iv1"),
    ("RESTAPIv2", "restapiv2", "restap_iv2"),
    ("HTTPAPIKey", "httpapi_key", "httpapi_key"),  # Works correctly with full word
    ("getAPIv2", "get_apiv2", "get_ap_iv2"),
]

print("Demonstrating the bug:")
for input_str, expected, _ in test_cases:
    actual = camel_to_snake(input_str)
    print(f"  camel_to_snake('{input_str}') = '{actual}'")
    print(f"    Expected: '{expected}'")
    print(f"    Got:      '{actual}'")
    print(f"    Bug:      {'YES' if actual != expected else 'NO'}\n")

print("\nThe issue:")
print("When 3+ consecutive uppercase letters are followed by a lowercase letter,")
print("the regex incorrectly places an underscore between the last two uppercase")
print("letters, splitting acronyms like 'API' into 'ap_i'.")