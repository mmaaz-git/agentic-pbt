#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/praw_env/lib/python3.13/site-packages')

import re
from praw.util import camel_to_snake

print("Investigating potential bug in camel_to_snake...")
print("\nAnalyzing how the regex works...")

# Let's understand the regex pattern
_re_camel_to_snake = re.compile(r"([a-z0-9](?=[A-Z])|[A-Z](?=[A-Z][a-z]))")

test_string = "APIv2"
print(f"\nInput: '{test_string}'")

# Step by step analysis
matches = list(_re_camel_to_snake.finditer(test_string))
print(f"Regex matches: {[(m.group(), m.start(), m.end()) for m in matches]}")

# Manual step-by-step conversion
result = _re_camel_to_snake.sub(r"\1_", test_string)
print(f"After regex substitution: '{result}'")
print(f"After .lower(): '{result.lower()}'")
print(f"Actual camel_to_snake result: '{camel_to_snake(test_string)}'")

print("\n" + "="*60)
print("\nTesting various API-related patterns:")

api_tests = [
    # Input -> Expected -> Actual
    ("API", "api"),  # All caps
    ("Api", "api"),  # Title case
    ("api", "api"),  # Lower case
    ("getAPI", "get_api"),  # camelCase with API at end
    ("APIKey", "api_key"),  # API at start
    ("APIv1", "apiv1"),  # API with version 1 - what should this be?
    ("APIv2", "apiv2"),  # API with version 2 - what should this be?
    ("APIVersion", "api_version"),  # API with full word
    ("v2API", "v2_api"),  # version before API
    ("getAPIv2", "get_apiv2"),  # Combined
    ("HTTPAPIv2", "httpapiv2"),  # Multiple acronyms
    ("RESTAPIv2", "restapiv2"),  # REST API
    ("APIMethods", "api_methods"),  # API with regular word
    ("APIInterface", "api_interface"),  
]

for test_input, expected in api_tests:
    actual = camel_to_snake(test_input)
    status = "✓" if actual == expected else "✗"
    print(f"  {status} '{test_input}' -> '{actual}' (expected '{expected}')")

print("\n" + "="*60)
print("\nDetailed analysis of the bug:")

# The problematic case
buggy_input = "APIv2"
print(f"\nInput: '{buggy_input}'")

# Let's trace through character by character
for i, char in enumerate(buggy_input):
    print(f"  Position {i}: '{char}' - ", end="")
    if i < len(buggy_input) - 1:
        # Check if this position matches the regex
        # Pattern 1: [a-z0-9](?=[A-Z])
        if char.islower() or char.isdigit():
            if buggy_input[i+1].isupper():
                print(f"matches [a-z0-9](?=[A-Z]) - will add underscore after")
                continue
        # Pattern 2: [A-Z](?=[A-Z][a-z])
        if char.isupper():
            if i < len(buggy_input) - 2:
                if buggy_input[i+1].isupper() and buggy_input[i+2].islower():
                    print(f"matches [A-Z](?=[A-Z][a-z]) - will add underscore after")
                    continue
    print("no match")

print("\n" + "="*60)
print("\nHypothesis about the bug:")
print("The regex pattern adds an underscore after 'I' in 'APIv2' because:")
print("- 'I' is uppercase")
print("- It's followed by 'v' (lowercase)")
print("- But 'I' is preceded by 'P' (uppercase), not matching the second pattern")
print("- The regex doesn't handle this case correctly for consecutive uppercase letters")
print("  followed by a lowercase letter when there are 3+ uppercase letters")

print("\n" + "="*60)
print("\nChecking if this is intentional or a bug...")

# Look at use cases - how would APIs typically name things?
common_patterns = [
    ("XMLHttpRequest", "xml_http_request"),  # Standard camelCase for web APIs
    ("HTMLElement", "html_element"),
    ("HTTPSConnection", "https_connection"),
    ("URLPath", "url_path"),
    ("IOError", "io_error"),
    # These show the pattern works for 2-4 letter acronyms normally
    
    # But what about with version numbers?
    ("APIv1", "apiv1"),  # Expected based on pattern?
    ("APIv2", "apiv2"),  # Expected based on pattern?
    
    # The actual results:
    ("APIv1", camel_to_snake("APIv1")),
    ("APIv2", camel_to_snake("APIv2")),
]

print("\nComparing expected patterns:")
for input_str, expected in common_patterns[-4:]:
    print(f"  '{input_str}' -> '{expected}'")

print("\n" + "="*60)
print("\nConclusion:")
print("The conversion 'APIv2' -> 'ap_iv2' appears to be a BUG because:")
print("1. It incorrectly splits 'API' into 'ap_i'")
print("2. The regex fails to handle the pattern of 3+ uppercase letters followed by lowercase")
print("3. This produces unintuitive results for common patterns like APIv2, RESTAPIv1, etc.")
print("4. Users would expect 'APIv2' -> 'apiv2' or 'api_v2', not 'ap_iv2'")