"""Investigate why Response allows control chars but HTTPException doesn't"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from pyramid.response import Response
import pyramid.httpexceptions as httpexc

print("=== Investigating the Difference ===\n")

# Test 1: Direct header setting on Response
print("Test 1: Setting Location header directly on Response")
resp = Response()
try:
    resp.headers['Location'] = 'test\r\nInjected: true'
    print(f"Success! Headers: {dict(resp.headers)}")
except ValueError as e:
    print(f"Failed: {e}")

# Test 2: Using location parameter in Response constructor
print("\nTest 2: Using location parameter in Response constructor")
try:
    resp = Response(location='test\r\nInjected: true')
    print(f"Success! Location: {resp.location}")
except Exception as e:
    print(f"Failed: {e}")

# Test 3: HTTPException with location in kw
print("\nTest 3: HTTPFound with location parameter")
try:
    exc = httpexc.HTTPFound(location='test\r\nInjected: true')
    print(f"Success! Location: {exc.location}")
except ValueError as e:
    print(f"Failed: {e}")

# Test 4: Let's trace where the validation happens
print("\nTest 4: Checking where validation occurs")
print("Creating HTTPFound step by step...")
location_with_crlf = 'test\r\n'

try:
    print(f"  Creating with location='{repr(location_with_crlf)}'")
    exc = httpexc.HTTPFound(location=location_with_crlf)
except ValueError as e:
    print(f"  ValueError during construction: {e}")
    import traceback
    print("\nTraceback:")
    traceback.print_exc()