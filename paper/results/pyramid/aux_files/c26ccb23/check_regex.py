"""Check the VALID_TOKEN regex behavior"""

import sys
import re
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from pyramid.authentication import VALID_TOKEN

print("Testing VALID_TOKEN regex")
print(f"Pattern: {VALID_TOKEN.pattern}")

test_cases = [
    'À',  # Unicode letter
    'a',  # ASCII letter
    'A',  # ASCII uppercase
    '1',  # Digit first
    'a1',  # Letter then digit
    'Test123',  # Valid token
    'test-token',  # With dash
    'test_token',  # With underscore
    'test+token',  # With plus
    'test token',  # With space
    '',  # Empty
]

for token in test_cases:
    match = VALID_TOKEN.match(token)
    # Check if string is entirely ASCII letters, digits, +, -, _
    # and starts with a letter
    expected = (
        len(token) > 0 and
        token[0].isalpha() and 
        token[0].isascii() and
        all(c.isalnum() or c in '+_-' for c in token) and
        all(c.isascii() for c in token)
    )
    
    actual = match is not None
    status = "✓" if actual == expected else "✗ BUG"
    print(f"{status} Token: {repr(token):15} | Match: {actual:5} | Expected: {expected:5}")