"""Test how urlencode handles empty values."""

from urllib.parse import urlencode, quote

# Test empty value handling
params = {"key1": "value1", "key2": ""}
result = urlencode(params, quote_via=quote)
print(f"urlencode with empty value: {result}")

# Test what quote does with default safe parameter
print(f"\nquote('pass/word'): {quote('pass/word')}")  # Default safe='/'
print(f"quote('pass/word', safe=''): {quote('pass/word', safe='')}")  # No safe chars