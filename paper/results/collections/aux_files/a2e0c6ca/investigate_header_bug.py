import sys
import os
import datetime
import random
import string

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'venv/lib/python3.13/site-packages'))

from flask import Flask
from hypothesis import given, strategies as st, settings

print("=== Flask Header Validation Bug Investigation ===\n")

# Test case 1: Basic newline injection
app = Flask(__name__)

print("Test 1: Headers with newline characters")
print("-" * 40)

test_cases = [
    {'X-Custom': 'normal_value'},  # Control - should work
    {'X-Custom': 'value\n'},  # Trailing newline
    {'X-Custom': '\nvalue'},  # Leading newline
    {'X-Custom': 'value1\nX-Injected: value2'},  # Header injection attempt
    {'Content-Type': 'text/plain\r\n'},  # CRLF
]

for i, headers in enumerate(test_cases, 1):
    print(f"\nCase {i}: {headers}")
    with app.test_request_context():
        try:
            response = app.make_response(("body", headers))
            print(f"  ✓ Success - Headers accepted")
            print(f"  Response headers: {dict(response.headers)}")
        except ValueError as e:
            print(f"  ✗ ValueError: {e}")
        except Exception as e:
            print(f"  ✗ Unexpected error: {type(e).__name__}: {e}")

print("\n" + "=" * 50)
print("\nTest 2: Using 3-tuple with headers")
print("-" * 40)

with app.test_request_context():
    # Test with 3-tuple format
    try:
        response = app.make_response(("body", 200, {'X-Test': 'value\nX-Injected: evil'}))
        print("3-tuple with newline in headers: Success (UNEXPECTED)")
    except ValueError as e:
        print(f"3-tuple with newline in headers: ValueError (EXPECTED)")
        print(f"  Error: {e}")

print("\n" + "=" * 50)
print("\nTest 3: Property-based test to find all failing characters")
print("-" * 40)

@given(st.text())
@settings(max_examples=100)
def test_header_values(value):
    """Find all header values that cause errors"""
    app = Flask(__name__)
    with app.test_request_context():
        try:
            response = app.make_response(("body", {'X-Test': value}))
            return True
        except ValueError:
            return False

# Test specific problematic characters
problematic_chars = []
for char in ['\n', '\r', '\r\n', '\x00', '\t']:
    with app.test_request_context():
        try:
            response = app.make_response(("body", {'X-Test': f'value{char}'}))
        except ValueError:
            problematic_chars.append(repr(char))

print(f"Characters that cause ValueError in headers: {problematic_chars}")

print("\n" + "=" * 50)
print("\nConclusion:")
print("-" * 40)
print("Flask's make_response() method does NOT validate header values before")
print("passing them to Werkzeug's Headers class. This causes:")
print("1. Late error detection - errors occur deep in Werkzeug, not at Flask level")
print("2. Inconsistent error messages - Flask's error handling doesn't catch this")
print("3. Potential security implications if headers come from user input")
print("\nFlask should validate headers for newlines/carriage returns before")
print("passing to the response class to provide better error messages and")
print("earlier validation.")