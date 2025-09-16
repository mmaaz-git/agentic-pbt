"""Minimal reproductions of bugs found in google.api_core."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/google-cloud-recaptcha-enterprise_env/lib/python3.13/site-packages')

from google.api_core import protobuf_helpers
from google.api_core import path_template

print("Bug 1: protobuf_helpers.check_oneof error message formatting")
print("=" * 60)
try:
    # Keys with newlines break error message formatting
    protobuf_helpers.check_oneof(**{'0': 0, '\n': 0})
except ValueError as e:
    print(f"Error message: {e}")
    print(f"Repr: {repr(str(e))}")
    print("Issue: Newline in key name breaks message formatting")
print()

print("Bug 2: path_template.validate doesn't escape regex special characters")
print("=" * 60)

# Test case 1: Backslash at end causes regex to fail
template1 = '\\'
try:
    result = path_template.validate(template1, template1)
    print(f"validate('\\\\', '\\\\') = {result}")
    print("Issue: Should be True but returns False")
except Exception as e:
    print(f"Exception: {e}")

print()

# Test case 2: Opening bracket causes regex error
template2 = '['
try:
    result = path_template.validate(template2, template2)
    print(f"validate('[', '[') = {result}")
except Exception as e:
    print(f"Exception type: {type(e).__name__}")
    print(f"Exception: {e}")
    print("Issue: Regex special characters not escaped")

print()

# Test case 3: Backreference causes regex error  
template3 = '\\1'
try:
    result = path_template.validate(template3, template3)
    print(f"validate('\\\\1', '\\\\1') = {result}")
except Exception as e:
    print(f"Exception type: {type(e).__name__}")
    print(f"Exception: {e}")
    print("Issue: Backslash sequences interpreted as regex backreferences")