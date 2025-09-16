#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/praw_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, settings, assume
import string
from praw.util import camel_to_snake, snake_case_keys

print("Deep investigation of praw snake case conversion...")

# Test 1: Check if consecutive uppercase letters are handled correctly
print("\n1. Testing consecutive uppercase handling...")
test_cases = [
    ("XMLHttpRequest", "xml_http_request"),
    ("XMLHTTPRequest", "xmlhttp_request"),  
    ("IOError", "io_error"),
    ("IOException", "io_exception"),
    ("HTMLElement", "html_element"),
    ("PDFReader", "pdf_reader"),
    ("URLPath", "url_path"),
    ("HTTPSConnection", "https_connection"),
    ("HTTPResponse", "http_response"),
    ("getHTTPResponseCode", "get_http_response_code"),
    ("HTTPSProxy", "https_proxy"),
    ("XMLParser", "xml_parser"),
]

for input_str, expected in test_cases:
    result = camel_to_snake(input_str)
    status = "✓" if result == expected else "✗"
    print(f"  {status} '{input_str}' -> '{result}' (expected '{expected}')")

# Test 2: Check numbers in strings
print("\n2. Testing number handling...")
number_tests = [
    ("version2API", "version2_api"),
    ("HTML2PDF", "html2_pdf"),
    ("base64Encode", "base64_encode"),
    ("md5Hash", "md5_hash"),
    ("utf8String", "utf8_string"),
    ("v2API", "v2_api"),
    ("APIv2", "apiv2"),
    ("getV2", "get_v2"),
]

for input_str, expected in number_tests:
    result = camel_to_snake(input_str)
    status = "✓" if result == expected else "✗"
    print(f"  {status} '{input_str}' -> '{result}' (expected '{expected}')")

# Test 3: Edge cases with underscores
print("\n3. Testing underscore edge cases...")
underscore_tests = [
    ("_privateMethod", "_private_method"),
    ("__doublePrivate", "__double_private"),
    ("already_snake_case", "already_snake_case"),
    ("mixed_snakeCase", "mixed_snake_case"),
    ("SCREAMING_SNAKE_CASE", "screaming_snake_case"),
    ("_", "_"),
    ("__", "__"),
]

for input_str, expected in underscore_tests:
    result = camel_to_snake(input_str)
    status = "✓" if result == expected else "✗"
    print(f"  {status} '{input_str}' -> '{result}' (expected '{expected}')")

# Test 4: Property-based test for finding bugs with special patterns
print("\n4. Running property-based tests for edge cases...")

@given(st.text(alphabet=string.ascii_uppercase, min_size=2, max_size=10))
@settings(max_examples=100)
def test_all_uppercase(s):
    """Test all uppercase strings - these might produce unexpected results"""
    result = camel_to_snake(s)
    # Check if we get any double underscores (which might be a bug)
    if '__' in result and '__' not in s:
        print(f"  Bug? All uppercase '{s}' -> '{result}' (contains double underscore)")
        return False
    return True

test_all_uppercase()

# Test 5: Test mixed patterns
print("\n5. Testing mixed patterns...")
mixed_tests = [
    ("getXMLHTTPRequest", "get_xmlhttp_request"),
    ("newHTMLParser", "new_html_parser"),
    ("AAAAbbbb", "aaaabbbb"),  # Edge case
    ("AAA", "aaa"),
    ("aAAA", "a_aaa"),
    ("AAAa", "aaaa"),
    ("renderHTMLToString", "render_html_to_string"),
]

for input_str, expected in mixed_tests:
    result = camel_to_snake(input_str)
    status = "✓" if result == expected else "✗"
    print(f"  {status} '{input_str}' -> '{result}' (expected '{expected}')")

# Test 6: Non-ASCII and special characters
print("\n6. Testing special characters...")
special_tests = [
    ("", ""),  # Empty string
    ("a", "a"),  # Single char
    ("A", "a"),  # Single uppercase
    ("1", "1"),  # Single digit
    ("123", "123"),  # All digits
    ("getCaché", "get_caché"),  # Non-ASCII
]

for input_str, expected in special_tests:
    result = camel_to_snake(input_str)
    status = "✓" if result == expected else "✗"
    print(f"  {status} '{input_str}' -> '{result}' (expected '{expected}')")

print("\n" + "="*60)

# Final comprehensive test to find any crash scenarios
print("\nLooking for crash scenarios...")

@given(st.text(min_size=0, max_size=100))
@settings(max_examples=500)
def test_no_crash(s):
    """Ensure the function doesn't crash on any input"""
    try:
        result = camel_to_snake(s)
        # Also test it doesn't crash when used in snake_case_keys
        d = {s: 1}
        snake_case_keys(d)
        return True
    except Exception as e:
        print(f"  CRASH on input '{repr(s)}': {e}")
        raise

test_no_crash()
print("✓ No crash scenarios found")

print("\n" + "="*60)
print("Investigation complete!")