import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

# Test if this is a real issue that could affect users
from pyramid.encode import urlencode, url_quote

print("Testing surrogate character handling in pyramid.encode")
print("="*60)

# Surrogate characters can appear in user input in various ways:
# 1. From broken Unicode decoding
# 2. From malformed JSON
# 3. From user input in web forms

# Test case 1: Direct surrogate character
print("\nTest 1: Direct surrogate in urlencode")
try:
    # A user could pass this as a query parameter
    result = urlencode({chr(0xD800): 'value'})
    print(f"Success: {result}")
except UnicodeEncodeError as e:
    print(f"FAILED: {e}")

print("\nTest 2: Direct surrogate in url_quote")
try:
    result = url_quote(chr(0xD800))
    print(f"Success: {result}")
except UnicodeEncodeError as e:
    print(f"FAILED: {e}")

# Test if this could come from real user input
print("\nTest 3: Simulating user input with broken encoding")
# This could happen if someone sends malformed data to a web service
malformed_string = "test" + chr(0xD800) + "data"
try:
    result = urlencode({"user_input": malformed_string})
    print(f"Success: {result}")
except UnicodeEncodeError as e:
    print(f"FAILED: {e}")

print("\nTest 4: Check if parse_url_overrides is affected")
from pyramid.url import parse_url_overrides

class MockRequest:
    application_url = "http://example.com"

request = MockRequest()

# This could come from user-controlled input
try:
    kw = {'_query': {'search': chr(0xD800)}}
    app_url, qs, anchor = parse_url_overrides(request, kw)
    print(f"Success: {qs}")
except UnicodeEncodeError as e:
    print(f"FAILED: {e}")

print("\n" + "="*60)
print("CONCLUSION: These functions crash on surrogate characters")
print("This could cause DoS if user input contains surrogates")