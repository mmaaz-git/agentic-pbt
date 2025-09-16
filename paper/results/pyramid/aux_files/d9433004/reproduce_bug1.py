"""Reproduce the control character in location header bug"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

import pyramid.httpexceptions as httpexc

print("=== Bug Reproduction: Control Characters in Location Header ===\n")

# Test 1: Control character in location
print("Test 1: Creating HTTPFound with location containing \\r")
try:
    exc = httpexc.HTTPFound(location='0\r')
    print(f"Success: {exc}")
except ValueError as e:
    print(f"Error: {e}")

print("\nTest 2: Creating HTTPFound with normal location")
try:
    exc = httpexc.HTTPFound(location='http://example.com')
    print(f"Success: Location header = {exc.headers['Location']}")
except Exception as e:
    print(f"Error: {e}")

print("\nTest 3: Various control characters")
control_chars = ['\r', '\n', '\r\n', '\x00', '\x0b']
for char_repr in control_chars:
    try:
        exc = httpexc.HTTPFound(location=f'http://example.com/path{char_repr}')
        print(f"Success with {repr(char_repr)}: {exc.headers['Location']}")
    except ValueError as e:
        print(f"Failed with {repr(char_repr)}: {e}")

print("\n=== Analysis ===")
print("This appears to be a validation in WebOb that prevents control characters")
print("in headers. The question is: should pyramid.httpexceptions validate")  
print("the location parameter before passing it to Response?")