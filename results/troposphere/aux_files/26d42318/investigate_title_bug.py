import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import inspector

# Test case from hypothesis: title with just newline
test_cases = [
    '\n',       # Just newline
    ' ',        # Just space  
    '\t',       # Just tab
    '\r\n',     # Windows newline
    '  \n  ',   # Mixed whitespace
    '',         # Empty string
]

print("Testing title validation with whitespace-only strings:")
print("=" * 50)

for title in test_cases:
    print(f"Testing title: {repr(title)}")
    try:
        target = inspector.AssessmentTarget(title)
        print(f"  ✗ UNEXPECTED SUCCESS - Created object with title: {repr(target.title)}")
    except ValueError as e:
        print(f"  ✓ Raised ValueError as expected: {e}")
    print()

# Additional test - see what the validation regex actually is
import re
from troposphere import valid_names

print("The validation regex pattern:")
print(f"Pattern: {valid_names.pattern}")
print(f"Regex object: {valid_names}")
print()

# Test empty string specifically
print("Testing empty string behavior:")
title = ""
print(f"  bool(''): {bool('')}")
print(f"  not '': {not ''}")
print(f"  valid_names.match(''): {valid_names.match('')}")

# Test validation logic
def validate_title(title):
    """Reproduce the validation logic from troposphere"""
    if not title or not valid_names.match(title):
        raise ValueError('Name "%s" not alphanumeric' % title)
    return True

print("\nDirect validation tests:")
for title in ['', ' ', '\n', 'ValidName123']:
    print(f"Title {repr(title)}: ", end="")
    try:
        validate_title(title)
        print("VALID")
    except ValueError as e:
        print(f"INVALID - {e}")